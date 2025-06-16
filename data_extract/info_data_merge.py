import pandas as pd
import glob

all_parts = glob.glob('./product_info_data/*.csv')
df = pd.concat([pd.read_csv(f) for f in all_parts], ignore_index=True)
df.to_csv('./product_info_data/merged_data.csv', index=False)