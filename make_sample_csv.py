import numpy as np
import pandas as pd

np.random.seed(42)
n = 48
dates = pd.date_range('2021-01-01', periods=n, freq='MS')
t = np.arange(n)
months = dates.month

holiday_map = {1: 1, 3: 1, 4: 2, 5: 1, 6: 2, 10: 1, 12: 3}
holidays = np.array([holiday_map.get(m, 0) for m in months])
marketing = np.random.uniform(400, 1200, n).round(0)
price = (15 + 0.05 * t + np.random.normal(0, 0.3, n)).round(2)
discount = np.random.choice([0, 0, 0, 5, 10], n)
inflation = (5 + np.random.normal(0, 0.5, n)).round(2)
gdp = (5.5 + np.random.normal(0, 0.4, n)).round(2)
exchange_rate = (3650 + 3 * t + np.random.normal(0, 20, n)).round(0)

seasonal = 1 + 0.25 * np.sin(2 * np.pi * (months - 3) / 12)
sales = ((1000 + 15 * t) * seasonal
         + 0.3 * marketing
         - 30 * (price - 15)
         + 8 * discount
         + 40 * holidays
         + np.random.normal(0, 40, n)).round(0)

df = pd.DataFrame({
    'date': dates.strftime('%Y-%m-%d'),
    'sales': sales,
    'marketing_spend': marketing,
    'holidays': holidays,
    'price': price,
    'discount': discount,
    'inflation': inflation,
    'gdp': gdp,
    'exchange_rate': exchange_rate,
})
df.to_csv('sample_sales.csv', index=False)
print(f"Created sample_sales.csv with {len(df)} months")