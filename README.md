# DemandCast

DemandCast is a Django web app for forecasting monthly product demand. You upload a CSV of past sales. The app cleans the data, shows charts that explore it, and then trains three forecasting models (SARIMA, Prophet and XGBoost). It recommends the most accurate model and predicts sales for the next 6 months.

## Features

- **User accounts.** You can sign up, log in and log out. Each user sees only their own datasets.
- **CSV upload and cleaning.** The app checks that the file is valid. It removes duplicate rows and rows with unreadable dates, and combines the data into one row per month. It fills in missing months and missing values, and shows a report of everything it changed.
- **Exploratory data analysis.** Charts show:
  - the sales trend, with a 12-month rolling average
  - average sales for each month of the year
  - the sales broken down into trend, seasonal pattern and leftover noise
  - how strongly each factor correlates with sales
  - which factor is linked most strongly to sales
- **Forecasting.** Each model is tested on the last 6 known months and scored with MAE, RMSE and MAPE. The model with the lowest MAPE is recommended. Its forecast is shown with an 80% likely range.
- **Export.** You can download the forecast as a CSV file, which opens in Excel or Power BI.

## Tech stack

| Area | Tools |
|------|-------|
| Web framework | Django |
| Data handling | pandas, NumPy |
| Models | statsmodels (SARIMA), Prophet, XGBoost, scikit-learn |
| Charts | Plotly |
| Page styling | Bootstrap 5 (loaded from a CDN) |
| Database | SQLite |

## Getting started

### 1. Clone the repository and create a virtual environment

```bash
git clone <your-repo-url>
cd <repo-folder>
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **macOS users:** XGBoost needs the OpenMP library. Install it with [Homebrew](https://brew.sh):
> ```bash
> brew install libomp
> ```
> If OpenMP is missing, the app still runs, but the forecast page reports that XGBoost could not run.

### 2. Set up the database

```bash
python manage.py migrate
python manage.py createsuperuser   # optional: needed to use the admin site at /admin/
```

### 3. Run the app

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/, create an account and upload a CSV.

## Input CSV format

| Column | Required | Description |
|--------|----------|-------------|
| `date` | Yes | Any date format that can be read as a date. Several rows in the same month are combined into one. |
| `sales` | Yes | Units sold |
| `marketing_spend` | No | Marketing spend for the period |
| `holidays` | No | Number of holidays in the period |
| `price` | No | Average selling price |
| `discount` | No | Discount (%) |
| `inflation` | No | Inflation rate (%) |
| `gdp` | No | GDP growth (%) |
| `exchange_rate` | No | Exchange rate |

- The file needs **at least 24 months** of data, so that yearly patterns can be detected.
- Column names are not case-sensitive, and spaces around them are ignored. Any column not listed above is ignored.
- `sales`, `marketing_spend` and `holidays` are added up for each month. All other columns are averaged.

### Sample data

The repository includes [`sample_sales.csv`](sample_sales.csv), which has 48 months of made-up data. To generate it again, run:

```bash
python make_sample_csv.py
```

## How the forecast works

1. **Testing:** the last 6 months of data are held back. Each model trains on the remaining months and predicts those 6. Its predictions are then compared with the real sales.
2. **Choosing a model:** the model with the lowest MAPE (mean absolute percentage error) is marked as recommended.
3. **Forecasting:** each model is retrained on all the data and predicts the next 6 months.
4. **Future factor values:** future values of the other columns are unknown, so the app assumes:
   - `holidays` takes that calendar month's average from past years
   - every other factor stays at its average over the last 3 months

| Model | Approach |
|-------|----------|
| SARIMA | Statistical model with yearly seasonality, `(1,1,1)(0,1,1,12)` |
| Prophet | Meta's forecasting library, with each factor added as a regressor |
| XGBoost | Gradient boosting. It predicts the change from the same month last year, using the month, sales from 6 months earlier, and the factors. |

## Configuration

Settings are read from environment variables. With none set, the app runs in local development mode.

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | insecure dev key | **Set this in production.** |
| `DJANGO_DEBUG` | `1` | Set to `0` in production |
| `DJANGO_ALLOWED_HOSTS` | *(empty)* | Comma-separated host names, for example `example.com,www.example.com` |

To generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Project structure

```
├── demandcast/          # Project settings and root URLs
├── accounts/            # Sign-up view
├── forecasting/
│   ├── preprocess.py        # CSV checking and cleaning
│   ├── eda.py               # Summary statistics and exploratory charts
│   ├── forecast_models.py   # SARIMA, Prophet and XGBoost, scoring, forecast charts
│   ├── models.py            # Dataset, ForecastRun and ForecastPoint
│   └── views.py
├── templates/           # HTML templates (base, auth, forecasting pages)
├── make_sample_csv.py   # Generates sample_sales.csv
├── sample_sales.csv
├── requirements.txt
└── manage.py
```

Uploaded files are saved in `media/datasets/`. That folder and the SQLite database are excluded from git.
