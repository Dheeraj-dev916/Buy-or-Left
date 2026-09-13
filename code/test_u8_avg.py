import os
import pandas as pd
import numpy as np

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u8 = events[events['user_id'] == 'user_08'].copy()
u8['event_date'] = pd.to_datetime(u8['event_date'])

# Look at average monthly spending by category for user 08
print("User 08 category monthly stats (count / sum / mean):")
u8_debits = u8[u8['direction'] == 'debit']
for cat, grp in u8_debits.groupby('category'):
    print(f"{cat:20s}: total={grp['amount'].sum():8.2f}, count={len(grp):2d}, mean={grp['amount'].mean():6.2f}, per_month={grp['amount'].sum()/6:6.2f}")
