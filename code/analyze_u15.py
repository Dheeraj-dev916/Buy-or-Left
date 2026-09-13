import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u15 = events[events['user_id'] == 'user_15'].copy()

print("User 15 all events:")
print(u15[['event_id', 'category', 'description', 'amount', 'event_date', 'status', 'flexibility']].sort_values('event_date').to_string())
