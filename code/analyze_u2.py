import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u2 = events[events['user_id'] == 'user_02'].copy()

# Look at pending events
print("Pending events:")
print(u2[u2['status'] == 'pending'][['event_id', 'description', 'category', 'amount', 'settlement_date']])

# Look at monthly expenses and their day of month
u2['day'] = pd.to_datetime(u2['event_date']).dt.day
print("\nExpenses by day of month and category:")
for cat, grp in u2[u2['direction'] == 'debit'].groupby('category'):
    print(f"Cat: {cat} (count {len(grp)}), days={sorted(grp['day'].unique())}, amounts={grp['amount'].unique()}")
