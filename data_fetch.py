import pandas as pd
from pymongo import MongoClient

db = MongoClient('mongodb://localhost:27017')['underlying']

def get_collections():
    return db.list_collection_names()

def get_data(stock):
    return pd.DataFrame(list(db[stock].find())).drop(columns = ['_id', 'symbol'])
    # return pd.DataFrame(list(db[stock].find())).drop(columns = '_id').to_dict(orient = 'records')

def make_data(df, index = None):
    if index:
        pass
    else:
        base = df.iloc[0].close
        df['baseChange'] = df.close.apply(lambda x : round((x - base) / base * 100, 2))
        # df.date = pd.to_datetime(df['date'], format = '%Y-%m-%d')
        # df.set_index(df['date'], inplace = True)
        df.set_index(pd.to_datetime(df['date'], format = '%Y-%m-%d'), inplace = True)
        return df[['date', 'baseChange']].to_dict(orient = 'records')