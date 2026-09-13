import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
msgs = pd.read_csv(os.path.join(data_dir, 'messages.csv'))

print(f"Total messages: {len(msgs)}")
print("Source types:", msgs['source_type'].value_counts().to_dict())
print("Non-null request_id:", msgs['request_id'].notna().sum())
print("Non-null user_id:", msgs['user_id'].notna().sum())
print("Non-null related_event_id:", msgs['related_event_id'].notna().sum())

# Sample of each source_type
for st, grp in msgs.groupby('source_type'):
    print(f"\n=== Source Type: {st} (count {len(grp)}) ===")
    for _, r in grp.head(4).iterrows():
        print(f"User: {r['user_id']}, Req: {r['request_id']}, Event: {r['related_event_id']}, Sent: {r['sent_at']}")
        print(f"Text: {r['message_text']}")
