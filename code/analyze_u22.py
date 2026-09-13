import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u22 = events[events['user_id'] == 'user_22'].copy()

print("User 22 all debit events:")
debits = u22[u22['direction'] == 'debit'].sort_values('event_date')
print(debits[['event_id', 'category', 'description', 'amount', 'event_date', 'status', 'flexibility']].to_string())
