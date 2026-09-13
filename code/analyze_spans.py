import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))

for idx, r in samples.head(5).iterrows():
    u = r['user_id']
    req_date = pd.to_datetime(r['request_date'])
    ue = events[events['user_id'] == u].copy()
    ue['dt'] = pd.to_datetime(ue['event_date'])
    print(f"User {u} (Req date: {r['request_date']}):")
    print(f"  Min date: {ue['dt'].min()}, Max date: {ue['dt'].max()}")
    print(f"  Events on/after req_date: {len(ue[ue['dt'] >= req_date])}")
    print(f"  Events in last 30 days before req_date: {len(ue[(ue['dt'] < req_date) & (ue['dt'] >= req_date - pd.Timedelta(days=30))])}")
