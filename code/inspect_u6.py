import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u6_events = events[events['user_id'] == 'user_06'].sort_values('event_date')

print("All event categories and descriptions for user_06:")
print(u6_events[['event_id', 'event_type', 'description', 'category', 'direction', 'amount', 'currency', 'event_date', 'status', 'flexibility', 'minimum_allowed_amount']].to_string())
