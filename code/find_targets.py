import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))

for u, target in [('user_22', 157.0), ('user_21', 568.0), ('user_18', 624.0), ('user_08', 452.0)]:
    ue = events[events['user_id'] == u]
    print(f"\n=== User {u} (Target diff: {target}) ===")
    print("Fixed/recurring debits:")
    # look at unique amounts
    debits = ue[ue['direction'] == 'debit']
    print(debits.groupby(['category', 'flexibility', 'description'])['amount'].unique())
