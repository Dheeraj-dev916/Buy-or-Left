import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
merged = samples.merge(profiles, on='user_id')

for idx, r in merged.iterrows():
    print(f"=== {r['request_id']} ({r['user_id']}) req_date={r['request_date']} amt={r['requested_amount']} comp_date={r['desired_completion_date']} ===")
    print(f"Text: {r['request_text']}")
    print(f"Status: {r['affordability_status']} | Method: {r['recommended_payment_method']} | Safe: {r['amount_safe_to_pay']} | Earliest: {r['earliest_date_for_full_payment']}")
    print(f"Plan: {r['payment_plan']}")
    print(f"Changes: {r['spending_changes_needed']}")
    print(f"Explanation: {r['decision_explanation']}")
    print(f"Balance: cur={r['current_available_balance']}, min={r['minimum_balance_to_keep']}")
    print(f"Consider: {r['payment_methods_user_will_consider']} | Protect: {r['expense_categories_to_protect']}")
    print()
