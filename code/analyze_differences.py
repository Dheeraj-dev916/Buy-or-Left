import os
import pandas as pd
import numpy as np

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
options = pd.read_csv(os.path.join(data_dir, 'request_payment_options.csv'))
messages = pd.read_csv(os.path.join(data_dir, 'messages.csv'))

# Map known image amounts
img_amounts = {
    'event_253': 4365000.0,
    'event_1442': 100000.0,
    'event_1545': 41272.0,
    'event_1700': 2854.0,
    'event_1786': 704.05,
    'event_3051': 1995.0,
    'event_3231': 8528.0,
    'event_4535': 15339.0,
    'event_5170': 723.0,
    'event_6033': 79679.26,
    'event_6859': 3650.0,
    'event_7307': 33.50,
    'event_7941': 2298.0,
    'event_9421': 4543.0,
    'event_9806': 9968.0,
    'event_10521': 393.22,
}

for ev_id, amt in img_amounts.items():
    events.loc[events['event_id'] == ev_id, 'amount'] = amt

# Let's check sample 1 to 5 differences
for idx, r in samples.head(10).iterrows():
    u_id = r['user_id']
    req_date = r['request_date']
    prof = profiles[profiles['user_id'] == u_id].iloc[0]
    curr_bal = prof['current_available_balance']
    min_bal = prof['minimum_balance_to_keep']
    headroom = curr_bal - min_bal
    safe = r['amount_safe_to_pay']
    diff = headroom - safe
    print(f"{r['request_id']} ({u_id}): cur_bal={curr_bal}, min_bal={min_bal}, headroom={headroom:.2f}, safe={safe}, diff={diff:.2f}")
