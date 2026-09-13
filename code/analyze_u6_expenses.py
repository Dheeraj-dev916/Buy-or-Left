import os
import pandas as pd

data_dir = os.path.abspath(os.path.join(os.getcwd(), '..', 'dataset'))
events = pd.read_csv(os.path.join(data_dir, 'financial_events.csv'))
u6 = events[events['user_id'] == 'user_06'].copy()

# Look at all expenses by category
print(u6.groupby(['category', 'flexibility'])['amount'].agg(['count', 'sum', 'mean', 'min', 'max']))

# Look at recurring fixed expenses
print("\nIndividual transactions:")
print(u6[['event_id', 'category', 'description', 'amount', 'event_date', 'status', 'flexibility']].sort_values('event_date').to_string())
