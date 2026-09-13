import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))

for req_id in ['request_08', 'request_03', 'request_05']:
    r = samples[samples['request_id'] == req_id].iloc[0]
    u = r['user_id']
    req_date = r['request_date']
    print(f"================== {req_id} ({u}) req_date={req_date} ==================")
    u_events = events[events['user_id'] == u].copy()
    print("Distinct categories & flexibilities:")
    print(u_events.groupby(['category', 'direction', 'flexibility'])['amount'].agg(['count', 'sum', 'mean']))
    print("\nPending or scheduled events:")
    print(u_events[u_events['status'].isin(['pending', 'scheduled'])][['event_id', 'description', 'category', 'direction', 'amount', 'event_date', 'settlement_date', 'status']])
    print("\nLatest events before req_date:")
    print(u_events.sort_values('event_date').tail(15)[['event_id', 'description', 'category', 'direction', 'amount', 'event_date', 'settlement_date', 'status', 'flexibility']])
