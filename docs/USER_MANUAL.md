# DemandCast User Manual

DemandCast predicts how much of a product you are likely to sell over the next 6 months, based on your past sales. You don't need any technical or statistics knowledge to use it.

**Contents**
1. [Create an account](#1-create-an-account)
2. [Log in and log out](#2-log-in-and-log-out)
3. [Prepare your sales file](#3-prepare-your-sales-file)
4. [Upload your data](#4-upload-your-data)
5. [Check your data](#5-check-your-data)
6. [Explore your data](#6-explore-your-data)
7. [Get a forecast](#7-get-a-forecast)
8. [Download the forecast](#8-download-the-forecast)
9. [Troubleshooting](#9-troubleshooting)
10. [Glossary](#10-glossary)

---

## 1. Create an account

You need an account before you can use the app. Your data is private: other users can't see your datasets.

1. Open DemandCast in your web browser.
2. Click **Sign up** in the top-right corner.
3. On the **Create an account** page, fill in:
   - **Username:** up to 150 characters. Letters, numbers and `@ . + - _` are allowed.
   - **Password:** see the rules below.
   - **Password confirmation:** type the same password again.
4. Click **Sign up**.

You are logged in automatically and taken to your home page.

**Password rules**
- At least 8 characters long
- Not too similar to your username
- Not a common password such as `password123`
- Not made of numbers only

> **Keep your password safe.** The app has no "forgot password" option. If you lose your password, ask the app administrator to reset it.

---

## 2. Log in and log out

### Log in
1. Click **Log in** in the top-right corner.
2. Enter your **Username** and **Password**.
3. Click **Log in**.

If you don't have an account yet, click **Sign up** under the login form.

### Log out
Click **Log out** in the top-right corner, next to "Hi, *your name*". Always log out when using a shared computer.

---

## 3. Prepare your sales file

DemandCast reads **CSV files**. You can make one in Excel or Google Sheets with **File → Save As / Download → CSV**.

### What the file must contain

| Column name | Required? | What to put in it |
|-------------|-----------|-------------------|
| `date` | **Yes** | The date of the sale or period, for example `2024-01-31` |
| `sales` | **Yes** | Number of units sold |
| `marketing_spend` | No | Money spent on marketing |
| `holidays` | No | Number of public holidays in the period |
| `price` | No | Average selling price |
| `discount` | No | Discount given, in % |
| `inflation` | No | Inflation rate, in % |
| `gdp` | No | GDP growth, in % |
| `exchange_rate` | No | Currency exchange rate |

### Rules
- The file needs **at least 24 months** of sales history, so the app can see yearly patterns. More data usually gives better forecasts.
- The first row must contain the column names exactly as shown above. Capital letters and extra spaces are fine.
- You can have one row per month, per week or per day. The app combines them into monthly totals.
- Any other columns are ignored.
- The optional columns help the app understand *why* sales go up and down. Include them if you have them.

### Example

```
date,sales,marketing_spend,holidays,price
2022-01-01,1020,800,1,15.00
2022-02-01,1105,650,0,15.10
2022-03-01,1240,900,1,15.05
...
```

> **Tip:** to try the app before using your own data, upload `sample_sales.csv` from the project folder. It contains 48 months of example data.

---

## 4. Upload your data

1. On your home page, click **+ Upload sales data**.
2. In **Product name**, type a name for this dataset, for example `Bottled Water 500ml`.
3. Under **Sales CSV file**, click **Choose file** and select your CSV.
4. Click **Upload and check**.

The app checks the file straight away. If something is wrong, an error message tells you what to fix (see [Troubleshooting](#9-troubleshooting)). If the file is OK, you see the message **"File uploaded and cleaned successfully."**

Every dataset you upload is listed on your **home page**. Click **Open** next to a dataset to return to it at any time.

---

## 5. Check your data

After uploading, you see the dataset page. It has three sections.

### Cleaning report
The app tidies your data automatically and tells you what it changed:

| Line | Meaning |
|------|---------|
| Rows uploaded | Number of rows in your file |
| Duplicate rows removed | Identical rows that appeared more than once |
| Rows with bad dates removed | Rows whose date could not be read |
| Missing months filled | Months that were missing from your timeline and were added |
| Missing values filled | Empty cells that were estimated from the months before and after |
| **Months ready for forecasting** | How many months of clean data the app will use |

If a lot of values were removed or filled in, check your original file. The forecast is only as good as the data.

### Summary statistics
For each column: the count, average (mean), spread (std), lowest (min), highest (max) and quartiles.

### Preview
The first 12 months of your cleaned data.

From here you can:
- click **Explore data (EDA)** to see charts and insights (section 6)
- click **Forecast demand** to go straight to the forecast (section 7)
- click **Back** to return to your home page

---

## 6. Explore your data

Click **Explore data (EDA)** on the dataset page. This page helps you understand your sales before forecasting.

### Key figures
| Figure | Meaning |
|--------|---------|
| Total sales | All units sold in the whole period |
| Monthly average | Average units sold per month |
| Growth (last 12 months) | Change in sales over the last 12 months compared with the 12 months before. Shown in green if sales went up, red if they went down. |
| Busiest month | The calendar month with the highest average sales |
| Quietest month | The calendar month with the lowest average sales |

### Key insight
If your file has optional columns, the blue box tells you which one is most closely linked to sales. For example: *"marketing spend is most closely linked to sales. Sales tend to rise when marketing spend goes up."*

### Charts
All charts are interactive:
- Hover over a point to see its value.
- Drag across part of a chart to zoom in. Double-click to zoom back out.
- Click a name in the legend to hide or show that line.

| Chart | What it shows |
|-------|---------------|
| **Sales over time** | Monthly sales, plus a 12-month average line that shows the overall direction |
| **Average sales by month** | Which months of the year are usually busy or quiet |
| **Trend / Seasonal / Residual** | Sales split into the long-term direction, the pattern that repeats every year, and the random ups and downs that are left over |
| **How factors relate to each other** | How strongly each pair of columns moves together. Values near **+1** rise together. Values near **−1** move in opposite directions. Values near **0** have little connection. |

---

## 7. Get a forecast

1. From the dataset page or the EDA page, click **Forecast demand**.
2. Click **Run forecast**.
3. Wait while the button shows *"Training models, please wait..."*. This can take up to a minute. Don't close the page.

The app tries **three different forecasting methods** (SARIMA, Prophet and XGBoost). It tests each one by predicting your last 6 known months and comparing the predictions with what really happened. The most accurate method is recommended.

### Reading the results

**Recommended model (green box):** which method was most accurate, and how far off it was on average. For example, *"off by about 5.1% … (94.9% accuracy)"*.

**Forecast chart:** your past sales (black line) followed by each method's prediction for the next 6 months. The recommended method is a thick solid line, with a shaded **likely range**.

**Forecast table:** for each of the next 6 months:
- **Expected demand:** the most likely number of units
- **Likely range:** the low and high estimates. About 8 times out of 10, real sales should fall inside this range.

**Model comparison:** accuracy scores for all three methods. The recommended one is highlighted and marked ★. For every score, **lower is better**:

| Score | Meaning |
|-------|---------|
| MAE | Average miss, in units |
| RMSE | Like MAE, but counts large misses more heavily |
| MAPE | Average miss as a percentage |
| Accuracy | 100% minus MAPE |

**Accuracy check chart:** the last 6 real months next to what each method predicted for them. The closer the lines are, the better the method.

**Assumptions used for future months:** the app can't know your future marketing spend, prices and so on. It assumes they stay at their average over the last 3 months. Holidays use the usual number for each calendar month. If you expect big changes, for example a large marketing campaign, keep in mind that the forecast doesn't include them.

### Running the forecast again
Click **Re-run forecast** at any time. This replaces the previous results. To forecast new data, upload it as a new dataset (section 4).

---

## 8. Download the forecast

Under the forecast table, click **Download forecast CSV (opens in Excel or Power BI)**.

The file contains one row per month for each method that ran successfully:

| Column | Meaning |
|--------|---------|
| month | The forecast month (YYYY-MM) |
| model | SARIMA, Prophet or XGBoost |
| best_model | `yes` for the recommended method |
| predicted | Expected demand |
| lower / upper | The likely range |

> **Tip:** to see only the recommended forecast in Excel, filter the `best_model` column to `yes`.

---

## 9. Troubleshooting

| Message or problem | What to do |
|--------------------|------------|
| **"Please upload a .csv file."** | Save your spreadsheet as CSV, then upload it again. Excel (.xlsx) files aren't accepted. |
| **"Missing required column(s): …"** | Make sure the first row contains column headers named `date` and `sales`. |
| **"Only N months of data found. Please upload at least 24 months…"** | Add more history. The app needs at least 2 years. |
| **"Could not read this file. Is it a valid CSV?"** | Open the file in a text editor to check it is comma-separated. Re-save it from Excel as **CSV (Comma delimited)**. |
| Your password is rejected at sign-up | Check the password rules in section 1. |
| **"These models could not run: …"** | One method failed, but you can still use the results of the others. If XGBoost keeps failing, tell the app administrator, who may need to install an extra component. |
| **"All models failed."** | Check the error in the model comparison table. Make sure your sales data has no long runs of zeros or blanks, then click **Re-run forecast**. |
| The forecast looks unrealistic | Check the cleaning report for many filled values, and look at the "Sales over time" chart for unusual spikes. Fix those in your file and upload it again. |
| You are sent to the login page | Your session has ended. Log in again. Your datasets are still saved. |

---

## 10. Glossary

| Term | Meaning |
|------|---------|
| **Dataset** | One uploaded sales file, usually for one product |
| **EDA** | Exploratory Data Analysis: charts and statistics that help you understand your data |
| **Forecast** | A prediction of future sales |
| **Seasonality** | A pattern that repeats every year, for example higher sales every December |
| **Trend** | The long-term direction of sales, whether growing, shrinking or flat |
| **Correlation** | How closely two things move together, from −1 to +1 |
| **Likely range** | The band where real sales are expected to fall about 80% of the time |
| **SARIMA** | A classic statistical forecasting method that models trend and yearly patterns |
| **Prophet** | A forecasting method created by Meta (Facebook) that handles seasonality and extra factors well |
| **XGBoost** | A machine-learning method that learns from patterns in your data and its factors |
