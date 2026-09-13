import os
import pandas as pd
import numpy as np
import datetime

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
profiles = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
messages = pd.read_csv(os.path.join(data_dir, 'messages.csv'))

# Insert image amounts
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

def simulate_user(u, req_date_str, target_safe):
    prof = profiles[profiles['user_id'] == u].iloc[0]
    ue = events[events['user_id'] == u].copy()
    ue['event_date'] = pd.to_datetime(ue['event_date'])
    req_date = pd.to_datetime(req_date_str)
    
    # 1. Historical events before req_date
    hist = ue[ue['event_date'] < req_date]
    
    # 2. Extract monthly recurring items: find events that occur ~monthly on similar day
    # Let's inspect unique categories
    print(f"\n================ USER {u} (Req {req_date_str}, Target Safe: {target_safe}) ================")
    print("Protected:", prof['expense_categories_to_protect'])
    print("Reduce:", prof['expense_categories_user_is_willing_to_reduce'])
    print("Stop:", prof['expense_categories_user_is_willing_to_stop'])

simulate_user('user_22', '2024-12-05', 475.46)
simulate_user('user_21', '2026-04-03', 1543.35)
simulate_user('user_06', '2026-01-03', 603.30)
simulate_user('user_08', '2025-02-07', 284.57)
