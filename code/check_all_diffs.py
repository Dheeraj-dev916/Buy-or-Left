import os
import pandas as pd
import numpy as np

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))

# Check all 25 samples
for idx, r in samples.iterrows():
    u = r['user_id']
    req_id = r['request_id']
    req_date = r['request_date']
    p = profiles[profiles['user_id'] == u].iloc[0]
    cur_bal = p['current_available_balance']
    min_bal = p['minimum_balance_to_keep']
    headroom = cur_bal - min_bal
    safe = r['amount_safe_to_pay']
    diff = headroom - safe
    print(f"{req_id} ({u}) req_date={req_date} headroom={headroom:.2f} safe={safe:.2f} diff={diff:.2f}")
