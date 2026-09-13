import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))

# Look at pending debits for all 25 sample requests:
for idx, r in samples.iterrows():
    u = r['user_id']
    req_date = r['request_date']
    ue = events[events['user_id'] == u]
    pends = ue[(ue['status'] == 'pending') & (ue['direction'] == 'debit')]
    prof = profiles[profiles['user_id'] == u].iloc[0]
    headroom = prof['current_available_balance'] - prof['minimum_balance_to_keep']
    diff = headroom - r['amount_safe_to_pay']
    pend_sum = pends['amount'].sum()
    print(f"{r['request_id']} ({u}): headroom={headroom:.2f}, safe={r['amount_safe_to_pay']:.2f}, diff={diff:.2f}, pend_sum={pend_sum:.2f}, diff_minus_pend={diff - pend_sum:.2f}")
    if len(pends) > 0:
        print("  Pending:", pends[['event_id', 'description', 'amount', 'settlement_date']].to_dict(orient='records'))
