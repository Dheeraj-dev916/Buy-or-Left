import os
import pandas as pd
import numpy as np

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))

# Check for each sample request:
# What is the minimum balance over the 90 days?
# What is the minimum balance dip date?
# Let's inspect the explanation text for all 25 samples:
for idx, r in samples.iterrows():
    print(f"[{r['request_id']}] Safe: {r['amount_safe_to_pay']} | Expl: {r['decision_explanation']}")
