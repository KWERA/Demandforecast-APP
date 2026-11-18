import pandas as pd

REQUIRED = ['date', 'sales']
OPTIONAL = ['marketing_spend', 'holidays', 'price', 'discount',
            'inflation', 'gdp', 'exchange_rate']
SUM_COLS = ['sales', 'marketing_spend', 'holidays']
MIN_MONTHS = 24


def load_and_clean(file):
    """Read a CSV, validate it, clean it and return (df, report)."""
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    report = {'rows_uploaded': len(df)}

    # Keep only the columns we understand
    keep = REQUIRED + [c for c in OPTIONAL if c in df.columns]
    df = df[keep].copy()

    # Remove exact duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    report['duplicates_removed'] = before - len(df)

    # Convert dates, drop rows with unreadable dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    report['bad_dates_removed'] = int(df['date'].isna().sum())
    df = df.dropna(subset=['date'])

    # Convert all other columns to numbers
    value_cols = keep[1:]
    for col in value_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Combine into one row per month
    df['date'] = df['date'].dt.to_period('M').dt.to_timestamp()
    agg = {}
    for col in value_cols:
        if col in SUM_COLS:
            agg[col] = lambda s: s.sum(min_count=1)
        else:
            agg[col] = 'mean'
    df = df.groupby('date').agg(agg)

    # Add any missing months so the timeline has no gaps
    full_range = pd.date_range(df.index.min(), df.index.max(), freq='MS')
    report['missing_months_filled'] = len(full_range) - len(df)
    df = df.reindex(full_range)
    df.index.name = 'date'

    # Fill missing values by drawing a line between neighbours
    report['missing_values_filled'] = int(df.isna().sum().sum())
    df = df.interpolate(limit_direction='both')

    # Sales can't be negative
    df['sales'] = df['sales'].clip(lower=0)

    if len(df) < MIN_MONTHS:
        raise ValueError(
            f"Only {len(df)} months of data found. "
            f"Please upload at least {MIN_MONTHS} months so seasonality can be detected."
        )

    report['months_after_cleaning'] = len(df)
    report['start'] = df.index.min().strftime('%b %Y')
    report['end'] = df.index.max().strftime('%b %Y')
    return df.reset_index(), report