import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u8 = events[events['user_id'] == 'user_08'].copy()
u8['event_date'] = pd.to_datetime(u8['event_date'])
u8['day'] = u8['event_date'].dt.day

for cat, grp in u8.groupby('category'):
    print(f"Cat: {cat}")
    print(grp[['event_id', 'description', 'amount', 'day', 'status', 'flexibility']].drop_duplicates().to_string())
    print()
