import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
requests = pd.read_csv(os.path.join(data_dir, 'requests.csv'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))

print("Events min date:", events['event_date'].min(), "max date:", events['event_date'].max())
print("Samples min req_date:", samples['request_date'].min(), "max req_date:", samples['request_date'].max())
print("Requests min req_date:", requests['request_date'].min(), "max req_date:", requests['request_date'].max())

# How many events per user?
counts = events.groupby('user_id').size()
print(f"Events per user: min={counts.min()}, max={counts.max()}, median={counts.median()}")
