import os
import pandas as pd
import numpy as np

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
options = pd.read_csv(os.path.join(data_dir, 'request_payment_options.csv'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))

# Join sample with profile
m = samples.merge(profiles, on='user_id')

for idx, r in m.iterrows():
    print(f"Req: {r['request_id']} | User: {r['user_id']} | Cur: {r['home_currency']}")
    print(f"  Req Date: {r['request_date']} | Req Amt: {r['requested_amount']} | Desired Comp: {r['desired_completion_date']} | Partial: {r['allows_partial_payment']}")
    print(f"  Balance: {r['current_available_balance']} | Min Keep: {r['minimum_balance_to_keep']} | Excess: {r['current_available_balance'] - r['minimum_balance_to_keep']}")
    print(f"  Output Safe: {r['amount_safe_to_pay']} | Status: {r['affordability_status']} | Method: {r['recommended_payment_method']}")
    print(f"  Plan: {r['payment_plan']}")
    print(f"  Earliest Full: {r['earliest_date_for_full_payment']} | Spending Changes: {r['spending_changes_needed']}")
    print(f"  Will Consider: {r['payment_methods_user_will_consider']} | Max Install: {r['max_installment_months']}")
    print()
