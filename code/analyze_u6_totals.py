import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u6 = events[events['user_id'] == 'user_06'].copy()
u6['event_date'] = pd.to_datetime(u6['event_date'])

# For each month (Sept, Oct, Nov, Dec 2025):
for m in [9, 10, 11, 12]:
    sub = u6[(u6['event_date'].dt.month == m) & (u6['event_date'].dt.year == 2025)]
    debits = sub[sub['direction'] == 'debit']
    print(f"Month 2025-{m:02d}: Total Debits = {debits['amount'].sum():.2f}")
    # By category
    print(debits.groupby('category')['amount'].sum().to_dict())

# What about between Jan 3 and Jan 15?
# Let's check in Oct, Nov, Dec what was spent between the 3rd and 15th:
for m in [10, 11, 12]:
    sub = u6[(u6['event_date'].dt.month == m) & (u6['event_date'].dt.year == 2025) & (u6['event_date'].dt.day >= 3) & (u6['event_date'].dt.day <= 15)]
    debits = sub[sub['direction'] == 'debit']
    print(f"Month 2025-{m:02d} (days 3 to 15): Total Debits = {debits['amount'].sum():.2f}")
    print(debits[['event_id', 'category', 'amount', 'event_date']].to_string())
