import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))

msgs = pd.read_csv(os.path.join(data_dir, 'messages.csv'))
imgs = pd.read_csv(os.path.join(data_dir, 'images.csv'))

print(f"Total messages: {len(msgs)}")
print("Messages sample:")
print(msgs.head(15).to_string())

print(f"\nTotal images: {len(imgs)}")
print("Images list:")
print(imgs.to_string())
