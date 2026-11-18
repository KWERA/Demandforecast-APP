"""
Forecasting engine.

Each model function takes:
    history  : DataFrame with 'date', 'sales' and optional factor columns
    future   : DataFrame with 'date' and the same factor columns (no sales)
and returns a DataFrame with 'date', 'predicted', 'lower', 'upper'.
"""
import logging
import warnings

import numpy as np
import pandas as pd

HORIZON = 6          # months to forecast
Z_80 = 1.28          # 80% confidence band



def factor_columns(df):
    """All columns except date and sales (marketing, price, etc.)."""
    return [c for c in df.columns if c not in ('date', 'sales')]


def future_factors(df, horizon=HORIZON):
    """
    Build the next `horizon` months with assumed factor values.
    Holidays: same month's average from past years.
    Everything else: average of the last 3 months.
    """
    start = df['date'].max() + pd.offsets.MonthBegin(1)
    future = pd.DataFrame({'date': pd.date_range(start, periods=horizon, freq='MS')})
    for col in factor_columns(df):
        if col == 'holidays':
            by_month = df.groupby(df['date'].dt.month)['holidays'].mean()
            future[col] = future['date'].dt.month.map(by_month).fillna(0)
        else:
            future[col] = df[col].iloc[-3:].mean()
    return future


# ---------------------------------------------------------------- SARIMA
def sarima_forecast(history, future):
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    y = history.set_index('date')['sales'].asfreq('MS')
    model = SARIMAX(y, order=(1, 1, 1), seasonal_order=(0, 1, 1, 12),
                    enforce_stationarity=False, enforce_invertibility=False)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        result = model.fit(disp=False)
    fc = result.get_forecast(steps=len(future))
    ci = fc.conf_int(alpha=0.2)
    return pd.DataFrame({
        'date': future['date'].values,
        'predicted': fc.predicted_mean.values,
        'lower': ci.iloc[:, 0].values,
        'upper': ci.iloc[:, 1].values,
    })


# ---------------------------------------------------------------- Prophet
def prophet_forecast(history, future):
    from prophet import Prophet
    logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
    logging.getLogger('prophet').setLevel(logging.ERROR)

    # Prophet reserves some names (like 'holidays'), so prefix ours with x_
    rename = {col: f'x_{col}' for col in factor_columns(history)}
    train = history.rename(columns={'date': 'ds', 'sales': 'y', **rename})
    model = Prophet(yearly_seasonality=True, weekly_seasonality=False,
                    daily_seasonality=False, interval_width=0.8)
    for col in rename.values():
        model.add_regressor(col)
    model.fit(train)
    pred = model.predict(future.rename(columns={'date': 'ds', **rename}))
    return pd.DataFrame({
        'date': future['date'].values,
        'predicted': pred['yhat'].values,
        'lower': pred['yhat_lower'].values,
        'upper': pred['yhat_upper'].values,
    })


# ---------------------------------------------------------------- XGBoost
def xgboost_forecast(history, future):
    """
    XGBoost learns how this year's sales differ from the same month last
    year, using the month, recent sales (6 months back) and the factors.
    """
    from xgboost import XGBRegressor

    factors = factor_columns(history)
    full = pd.concat([history, future.assign(sales=np.nan)], ignore_index=True)
    full['month'] = full['date'].dt.month
    full['lag_6'] = full['sales'].shift(6)
    full['lag_12'] = full['sales'].shift(12)
    full['target'] = full['sales'] - full['lag_12']

    features = ['month', 'lag_6'] + factors
    n = len(history)
    train = full.iloc[:n].dropna(subset=['lag_6', 'lag_12'])
    test = full.iloc[n:]

    model = XGBRegressor(n_estimators=300, max_depth=3, learning_rate=0.05,
                         subsample=0.9, random_state=42)
    model.fit(train[features], train['target'])
    predicted = test['lag_12'].values + model.predict(test[features])

    # XGBoost has no built-in range. run_all() fills lower/upper
    # using the model's error on the test months.
    return pd.DataFrame({
        'date': future['date'].values,
        'predicted': predicted,
        'lower': np.nan,
        'upper': np.nan,
    })


MODELS = {
    'SARIMA': sarima_forecast,
    'Prophet': prophet_forecast,
    'XGBoost': xgboost_forecast,
}


def _scores(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    err = actual - predicted
    mae = np.mean(np.abs(err))
    rmse = np.sqrt(np.mean(err ** 2))
    nonzero = actual != 0
    mape = np.mean(np.abs(err[nonzero] / actual[nonzero])) * 100 if nonzero.any() else None
    return round(mae, 2), round(rmse, 2), (round(mape, 2) if mape is not None else None)


def _no_negatives(frame):
    for col in ('predicted', 'lower', 'upper'):
        frame[col] = frame[col].clip(lower=0)
    return frame


def run_all(df, horizon=HORIZON):
    """
    1. Hide the last `horizon` months, train on the rest, and score each
       model against what really happened (the 'test').
    2. Retrain on all the data and forecast the next `horizon` months.
    Returns a list of result dicts, one per model.
    """
    train, test = df.iloc[:-horizon], df.iloc[-horizon:]
    future = future_factors(df, horizon)
    results = []

    for name, fn in MODELS.items():
        try:
            test_pred = fn(train, test.drop(columns='sales'))
            mae, rmse, mape = _scores(test['sales'], test_pred['predicted'])
            future_pred = fn(df, future)
            # Models without their own range get one from their test error
            for frame in (test_pred, future_pred):
                if frame['lower'].isna().any():
                    frame['lower'] = frame['predicted'] - Z_80 * rmse
                    frame['upper'] = frame['predicted'] + Z_80 * rmse
            test_pred = _no_negatives(test_pred)
            future_pred = _no_negatives(future_pred)
            results.append({'name': name, 'mae': mae, 'rmse': rmse, 'mape': mape,
                            'test': test_pred, 'future': future_pred, 'error': ''})
        except Exception as exc:
            results.append({'name': name, 'error': str(exc)[:500]})

    scored = [r for r in results if not r['error'] and r['mape'] is not None]
    if scored:
        best = min(scored, key=lambda r: r['mape'])
        best['is_best'] = True
    return results


# ---------------------------------------------------------------- Charts
COLORS = {'SARIMA': '#2563eb', 'Prophet': '#d97706', 'XGBoost': '#059669'}


def _points_frame(run, kind):
    rows = run.points.filter(kind=kind).values('date', 'predicted', 'lower', 'upper')
    frame = pd.DataFrame(list(rows))
    if not frame.empty:
        frame['date'] = pd.to_datetime(frame['date'])
    return frame


def forecast_chart(df, runs):
    """History plus each model's 6-month forecast, with the best model's range shaded."""
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['sales'], name='Actual sales',
                             mode='lines+markers', line=dict(color='#111827')))
    last_date, last_sales = df['date'].iloc[-1], df['sales'].iloc[-1]

    for run in runs:
        frame = _points_frame(run, 'future')
        if frame.empty:
            continue
        color = COLORS.get(run.model_name, '#6b7280')
        if run.is_best:
            fig.add_trace(go.Scatter(
                x=list(frame['date']) + list(frame['date'][::-1]),
                y=list(frame['upper']) + list(frame['lower'][::-1]),
                fill='toself', fillcolor='rgba(37, 99, 235, 0.12)', line=dict(width=0),
                name=f'{run.model_name} likely range', hoverinfo='skip'))
        # Start each forecast line from the last real month so it joins up
        fig.add_trace(go.Scatter(
            x=[last_date] + list(frame['date']),
            y=[last_sales] + list(frame['predicted']),
            name=f'{run.model_name}{" (best)" if run.is_best else ""}',
            mode='lines+markers',
            line=dict(color=color, width=3 if run.is_best else 1.5,
                      dash='solid' if run.is_best else 'dot')))

    fig.add_vline(x=last_date, line_dash='dash', line_color='#9ca3af')
    fig.update_layout(title='Sales history and 6-month forecast', template='plotly_white',
                      height=450, margin=dict(l=40, r=20, t=60, b=40),
                      legend=dict(orientation='h', y=-0.15))
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def test_chart(df, runs):
    """The last 6 known months: what really happened vs what each model guessed."""
    import plotly.graph_objects as go

    actual = df.iloc[-HORIZON:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=actual['date'], y=actual['sales'], name='Actual sales',
                             mode='lines+markers', line=dict(color='#111827', width=3)))
    for run in runs:
        frame = _points_frame(run, 'test')
        if frame.empty:
            continue
        fig.add_trace(go.Scatter(x=frame['date'], y=frame['predicted'], name=run.model_name,
                                 mode='lines+markers',
                                 line=dict(color=COLORS.get(run.model_name, '#6b7280'), dash='dot')))
    fig.update_layout(title='Accuracy check: predictions vs actual sales (last 6 months)',
                      template='plotly_white', height=400,
                      margin=dict(l=40, r=20, t=60, b=40),
                      legend=dict(orientation='h', y=-0.2))
    return fig.to_html(full_html=False, include_plotlyjs=False)
