import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))

def dump_sample(req_id):
    samples = pd.read_csv(os.path.join(data_dir, 'sample_requests.csv'))
    r = samples[samples['request_id'] == req_id].iloc[0]
    u = r['user_id']
    print(f"============================ {req_id} ({u}) ============================")
    print("REQUEST:")
    print(dict(r))
    
    profs = pd.read_csv(os.path.join(data_dir, 'financial_profiles.csv'))
    p = profs[profs['user_id'] == u].iloc[0]
    print("\nPROFILE:")
    print(dict(p))

    opts = pd.read_csv(os.path.join(data_dir, 'request_payment_options.csv'))
    uo = opts[opts['request_id'] == req_id]
    print("\nPAYMENT OPTIONS:")
    print(uo[['payment_option_id', 'payment_method', 'payment_amount', 'number_of_payments', 'first_payment_date', 'payment_frequency_days', 'financing_fee', 'total_payable_amount']])

    msgs = pd.read_csv(os.path.join(data_dir, 'messages.csv'))
    um = msgs[(msgs['user_id'] == u) | (msgs['request_id'] == req_id)]
    print("\nMESSAGES:")
    print(um[['message_id', 'sent_at', 'source_type', 'message_text']])

    events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
    ue = events[events['user_id'] == u]
    print(f"\nFINANCIAL EVENTS ({len(ue)} total):")
    # Show recurring events / summary
    print(ue.groupby(['category', 'direction', 'flexibility', 'status'])['amount'].agg(['count', 'sum', 'mean']))
    
    # Check pending / scheduled
    pend = ue[ue['status'].isin(['pending', 'scheduled'])]
    if len(pend) > 0:
        print("\nPending / scheduled:")
        print(pend[['event_id', 'description', 'category', 'direction', 'amount', 'event_date', 'settlement_date', 'status']])

dump_sample('request_02')
