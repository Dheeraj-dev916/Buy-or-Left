import os
import pandas as pd
import numpy as np

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))

# Fill image amounts
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

# For each sample, let's look at the days between req_date and next payday
for idx, r in samples.iterrows():
    u = r['user_id']
    req_date = pd.to_datetime(r['request_date'])
    prof = profiles[profiles['user_id'] == u].iloc[0]
    headroom = prof['current_available_balance'] - prof['minimum_balance_to_keep']
    diff = headroom - r['amount_safe_to_pay']
    
    ue = events[events['user_id'] == u]
    pends = ue[(ue['status'] == 'pending') & (ue['direction'] == 'debit')]['amount'].sum()
    rem_diff = diff - pends
    
    # Check salary day
    salary_events = ue[ue['category'] == 'salary']
    if len(salary_events) > 0:
        sal_days = pd.to_datetime(salary_events['event_date']).dt.day.unique()
        sal_amt = salary_events['amount'].iloc[-1]
    else:
        sal_days = []
        sal_amt = 0
    
    print(f"Sample {r['request_id']} ({u}): req_date={r['request_date']}, rem_diff={rem_diff:.2f}, sal_days={sal_days}, sal_amt={sal_amt}")
