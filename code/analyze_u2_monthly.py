import os
import pandas as pd
import numpy as np

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u2 = events[events['user_id'] == 'user_02'].copy()

# Look at events between July 5 and July 15, or June 5 and June 15, etc.
u2['event_date'] = pd.to_datetime(u2['event_date'])
for month in [4, 5, 6, 7]:
    sub = u2[(u2['event_date'].dt.month == month) & (u2['event_date'].dt.day >= 5) & (u2['event_date'].dt.day < 15) & (u2['direction'] == 'debit')]
    print(f"Month {month} (5th to 15th): total={sub['amount'].sum()}")
    print(sub[['event_id', 'description', 'category', 'amount', 'event_date']].to_string())
    print()
