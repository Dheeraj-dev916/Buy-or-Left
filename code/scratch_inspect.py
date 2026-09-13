import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))

def inspect_user(user_id, request_id):
    print(f"================ USER {user_id} / REQ {request_id} ================")
    # 1. Profile
    prof = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
    user_prof = prof[prof['user_id'] == user_id]
    print("--- Profile ---")
    print(user_prof.to_dict(orient='records'))

    # 2. Request
    reqs = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
    u_req = reqs[reqs['request_id'] == request_id]
    print("--- Request ---")
    print(u_req.to_dict(orient='records'))

    # 3. Payment options
    opts = pd.read_csv(os.path.join(data_dir, 'request_payment_options.csv'))
    u_opts = opts[opts['request_id'] == request_id]
    print("--- Payment Options ---")
    print(u_opts.to_string())

    # 4. Messages
    msgs = pd.read_csv(os.path.join(data_dir, 'messages.csv'))
    u_msgs = msgs[(msgs['user_id'] == user_id) | (msgs['request_id'] == request_id)]
    print("--- Messages ---")
    print(u_msgs.to_string())

    # 5. Images
    imgs = pd.read_csv(os.path.join(data_dir, 'images.csv'))
    u_imgs = imgs[(imgs['user_id'] == user_id) | (imgs['request_id'] == request_id)]
    print("--- Images ---")
    print(u_imgs.to_string())

    # 6. Financial events
    events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
    u_events = events[events['user_id'] == user_id]
    print(f"--- Financial Events ({len(u_events)} total) ---")
    print("Event types:", u_events['event_type'].value_counts().to_dict())
    print("Statuses:", u_events['status'].value_counts().to_dict())
    print("Categories:", u_events['category'].value_counts().to_dict())
    print("Flexibilities:", u_events['flexibility'].value_counts().to_dict())
    
    # Check pending or future events
    req_date = u_req.iloc[0]['request_date']
    print(f"Request date: {req_date}")
    future_events = u_events[u_events['event_date'] >= req_date]
    print(f"Events on/after req_date ({len(future_events)}):")
    print(future_events[['event_id', 'event_type', 'description', 'category', 'direction', 'amount', 'currency', 'event_date', 'settlement_date', 'status', 'flexibility', 'minimum_allowed_amount']].head(20).to_string())

inspect_user('user_01', 'request_01')
inspect_user('user_06', 'request_06')
