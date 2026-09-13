import os
import pandas as pd
import itertools

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u6 = events[events['user_id'] == 'user_06'].copy()

# Look at all amounts in u6
amounts = u6[u6['direction'] == 'debit']['amount'].tolist()

# Let's check subsets of December or recurring averages
print("Checking for exact match to 539.10:")
# Could it be max over past months of something?
# Or a specific set of categories?
dec = u6[(pd.to_datetime(u6['event_date']).dt.month == 12) & (u6['direction'] == 'debit')]
print("Dec items:")
for idx, r in dec.iterrows():
    print(f"{r['category']}: {r['amount']} ({r['event_date']})")
