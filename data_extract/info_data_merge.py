import pandas as pd
import glob
import os

def data_merge(category: str )-> None:
    dir_name = './merge_data'
    
    if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    all_parts = glob.glob('./product_info_data/*.csv')
    df = pd.concat([pd.read_csv(f) for f in all_parts], ignore_index=True)
    df.to_csv(f'./merge_data/merged_data_{category}.csv', index=False)