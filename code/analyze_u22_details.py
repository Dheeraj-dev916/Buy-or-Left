import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u22 = events[events['user_id'] == 'user_22'].copy()

print("User 22 all events summary:")
for cat, grp in u22.groupby('category'):
    print(f"Cat: {cat} (dir={grp['direction'].iloc[0]}, flex={grp['flexibility'].iloc[0]})")
    print("  Amounts:", grp['amount'].tolist())
    print("  Dates:", grp['event_date'].tolist())
