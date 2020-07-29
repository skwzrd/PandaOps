import redis
import pyarrow
import pandas as pd
import json
import subprocess

# local redis exe filepath: C:\\Users\Michael\AppData\Local\redis\64bit\redis-server.exe
# where to download redis for windows: https://github.com/dmajkic/redis/downloads
# how to store dataframes with redis: https://stackoverflow.com/a/57986261/9576988

class Cache:
    def __init__(self):
        self.r_context = pyarrow.default_serialization_context()

        self.configs = json.load(open('configs.json'))

        try:
            with open(self.configs['redis_log'], mode='w') as f:
                self.proc = subprocess.Popen(
                    self.configs['redis_server_exe_path'],
                    stdout=f
                )
        except Exception as e:
            print(e)
            raise e

        self.r = redis.Redis(host='localhost', port=6379, db=0)


    @staticmethod
    def make_df_key(key):
        """Serialized keys for dfs"""
        if key.startswith('df_'):
            return key
        return'df_'+key

    
    @staticmethod
    def make_df_key_d(key):
        """Deserializes key"""
        return key.replace('df_', '')


    def get_df_keys(self):
        """Gets all df keys from redis"""
        return [key.decode() for key in self.r.keys(pattern='df_*')]


    @staticmethod
    def get_df_keys_d(keys):
        """Deserializes given keys"""
        return [key.replace('df_', '') for key in keys]


    @staticmethod
    def is_df_key(key):
        """Does this qualify as a df key?"""
        if key is not None and key.startswith('df_'):
            return True
        return False


    def get_redis_df(self, key):
        """Given a key, returns a df from redis"""
        key = Cache.make_df_key(key)
        if self.redis_key_exists(key):
            df = self.r_context.deserialize(self.r.get(key))
            return df
        return None


    def get_selected_df(self):
        """Returns the selected df"""
        df_key = self.get_selected_df_key()
        df = self.get_redis_df(df_key)
        return df


    def add_redis_df(self, key, df):
        """Adds new df to redis, selects new df"""
        key = Cache.make_df_key(key)
        self.r.set(key, self.r_context.serialize(df).to_buffer().to_pybytes())
        self.set_selected_df(key)


    def delete_redis_dfs(self):
        """Deletes all dfs in redis"""
        for key in self.get_df_keys():
            print(f'Deleting df from cache: {key}')
            self.r.delete(key)


    def get_all_df_keys_d(self):
        """Returns list of df keys (names) from the session with the selected df at index 0."""
        df_keys = self.get_df_keys()
        df_keys = self.get_df_keys_d(df_keys)
        return df_keys


    def redis_key_exists(self, key):
        """Is a given key in redis"""
        if self.r.exists(key) > 0:
            return True
        return False


    def set_selected_df(self, key):
        """Given a key, this will be assigned as our selected df"""
        if Cache.is_df_key(key):
            self.r.set('selected_df', key)
        else:
            raise ValueError(f'Key {key} doesnt belong to df')


    def get_selected_df_key(self):
        """Returns our selected df key"""
        key = self.r.get('selected_df')
        if key:
            key = Cache.make_df_key(key.decode())
        return key

    
    def get_selected_df_key_d(self):
        """Returns our selected df key, deserialized"""
        key = self.r.get('selected_df')
        if key:
            key = Cache.make_df_key_d(key.decode())
        return key


    def get_and_select_df(self, key):
        """Gets df from redis with the given key.
            Makes the given key our selected df"""
        df = self.get_redis_df(key)
        self.set_selected_df(key)
        return df


    def get_sample_df(self):
        """Returns a sample df and makes it the selected df"""
        df = self.get_redis_df('df_Sample')
        if df is None:
            df = pd.DataFrame({
                'A': 1.,
                'B': pd.Timestamp('20130102'),
                'C': pd.Series(1, index=list(range(4)), dtype='float32'),
                'D': [3] * 4,
                'E': pd.Categorical(["test", "train", "test", "train"]),
                'F': 'foo'
            })
            self.add_redis_df('df_Sample', df)
        return df
