import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose


def _month_name(m, short=False):
    return pd.Timestamp(2000, m, 1).strftime('%b' if short else '%B')


def key_stats(df):
    s = df.set_index('date')['sales']
    by_month = s.groupby(s.index.month).mean()

    last12 = s.iloc[-12:].sum()
    prev12 = s.iloc[-24:-12].sum()
    growth = round((last12 - prev12) / prev12 * 100, 1) if prev12 else None

    return {
        'total': f"{s.sum():,.0f}",
        'average': f"{s.mean():,.0f}",
        'growth': growth,
        'best_month': _month_name(by_month.idxmax()),
        'worst_month': _month_name(by_month.idxmin()),
    }


def top_driver(df):
    num = df.drop(columns='date')
    if num.shape[1] < 2:
        return None
    corr = num.corr()['sales'].drop('sales').dropna()
    if corr.empty:
        return None
    name = corr.abs().idxmax()
    value = round(corr[name], 2)
    return {
        'name': name.replace('_', ' '),
        'value': value,
        'direction': 'rise' if value > 0 else 'fall',
    }


def trend_chart(df):
    d = df.copy()
    d['avg12'] = d['sales'].rolling(12, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d['date'], y=d['sales'], name='Monthly sales', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=d['date'], y=d['avg12'], name='12-month average', line=dict(dash='dash')))
    fig.update_layout(title='Sales over time')
    return fig


def seasonality_chart(df):
    d = df.copy()
    d['month'] = d['date'].dt.month
    avg = d.groupby('month')['sales'].mean().reset_index()
    avg['Month'] = avg['month'].apply(lambda m: _month_name(m, short=True))
    fig = px.bar(avg, x='Month', y='sales', title='Average sales by month (seasonality)')
    fig.update_yaxes(title='Average sales')
    return fig


def decomposition_chart(df):
    s = df.set_index('date')['sales']
    result = seasonal_decompose(s, model='additive', period=12)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=('Trend (long-term direction)',
                                        'Seasonal (repeating yearly pattern)',
                                        'Residual (unexplained noise)'))
    fig.add_trace(go.Scatter(x=s.index, y=result.trend), row=1, col=1)
    fig.add_trace(go.Scatter(x=s.index, y=result.seasonal), row=2, col=1)
    fig.add_trace(go.Scatter(x=s.index, y=result.resid, mode='markers'), row=3, col=1)
    fig.update_layout(showlegend=False)
    return fig


def correlation_chart(df):
    num = df.drop(columns='date')
    if num.shape[1] < 2:
        return None
    corr = num.corr().round(2)
    fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1, title='How factors relate to each other')
    return fig


def build_charts(df):
    figures = {
        'trend': (trend_chart(df), 400),
        'seasonality': (seasonality_chart(df), 400),
        'decomposition': (decomposition_chart(df), 650),
        'correlation': (correlation_chart(df), 550),
    }
    charts = {}
    first = True
    for key, (fig, height) in figures.items():
        if fig is None:
            continue
        fig.update_layout(template='plotly_white', height=height,
                          margin=dict(l=40, r=20, t=60, b=40))
        charts[key] = fig.to_html(full_html=False,
                                  include_plotlyjs='cdn' if first else False)
        first = False
    return charts