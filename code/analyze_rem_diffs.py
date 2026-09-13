import os
import pandas as pd
import numpy as np

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))

# Let's inspect the exact values for all 25 samples
for idx, r in samples.iterrows():
    u = r['user_id']
    p = profiles[profiles['user_id'] == u].iloc[0]
    headroom = p['current_available_balance'] - p['minimum_balance_to_keep']
    safe = r['amount_safe_to_pay']
    ue = events[events['user_id'] == u]
    pends = ue[(ue['status'] == 'pending') & (ue['direction'] == 'debit')]['amount'].sum()
    diff = headroom - safe
    rem = diff - pends
    print(f"Req {idx+1:02d} ({u}): Headroom={headroom:12.2f} | Safe={safe:12.2f} | Pends={pends:10.2f} | RemDiff={rem:12.2f}")
