import os
import pandas as pd
import redis
import pyarrow
from io import BytesIO
import subprocess
from flask import Flask, render_template, request, session, url_for

# local redis exe filepath: C:\\Users\Michael\AppData\Local\redis\64bit\redis-server.exe
# where to download redis for windows: https://github.com/dmajkic/redis/downloads
# how to store dataframes with redis: https://stackoverflow.com/a/57986261/9576988

redis_log = 'redis_output.txt'
redis_server_exe_path = r"C:\\Users\Michael\AppData\Local\redis\64bit\redis-server.exe"

with open(redis_log, mode='w') as f:
    proc = subprocess.Popen(
        redis_server_exe_path,
        stdout=f
    )

r = redis.Redis(host='localhost', port=6379, db=0)
r_context = pyarrow.default_serialization_context()


app = Flask(__name__, static_url_path='/static')


UPLOAD_FOLDER = 'UPLOAD_FOLDER'
ALLOWED_FILETYPES = {'.csv'}
app.config[UPLOAD_FOLDER] = 'static/temp'
app.config['SECRET_KEY'] = '123456'


# TODO
# ====
# check for duplicate records
# filter by column values
# refactor code into appropriate modules
# show/hide column dtypes
# convert column dtypes
# apply methods on dfs
# create/remove columns
# plot df's
# save plots
# save modified df's

# DONE
# ====
# replace df list dropdown with <ul>
# convert post requests to ajax
# rearrange buttons
# do not store df's in sessions (there is 4092 byte limit) - find something else
# clean up home()
# css styling (good enough for now)


def make_df_key(key):
    """Serialized keys for dfs"""
    if key.startswith('df_'):
        return key
    return'df_'+key


def get_df_keys():
    """Gets all df keys from redis"""
    return [key.decode() for key in r.keys(pattern='df_*')]


def get_df_keys_deserialized(keys):
    """Deserializes given keys"""
    return [key.replace('df_', '') for key in keys]


def is_df_key(key):
    """Does this qualify as a df key?"""
    if key is not None and key.startswith('df_'):
        return True
    return False


def get_redis_df(key):
    """Given a key, returns a df from redis"""
    key = make_df_key(key)
    if redis_key_exists(key):
        df = r_context.deserialize(r.get(key))
        return df
    return None


def add_redis_df(key, df):
    """Adds new df to redis, selects new df"""
    key = make_df_key(key)
    r.set(key, r_context.serialize(df).to_buffer().to_pybytes())
    set_selected_df(key)


def delete_redis_dfs():
    """Deletes all dfs in redis"""
    for key in get_df_keys():
        print(f'Deleting df from cache: {key}.')
        r.delete(key)


def get_all_df_keys_deserialized():
    """Returns list of df keys (names) from the session with the selected df at index 0."""
    df_keys = get_df_keys()
    df_keys = get_df_keys_deserialized(df_keys)
    return df_keys


def redis_key_exists(key):
    """Is a given key in redis"""
    if r.exists(key) > 0:
        return True
    return False


def set_selected_df(key):
    """Given a key, this will be assigned as our selected df"""
    if is_df_key(key):
        r.set('selected_df', key)
    else:
        raise ValueError(f'Key {key} doesnt belong to df')


def get_selected_df_key():
    """Returns our selected df key"""
    key = r.get('selected_df')
    if key:
        key = make_df_key(key.decode())
    return key


def get_and_select_df(key):
    """Gets df from redis with the given key.
        Makes the given key our selected df"""
    df = get_redis_df(key)
    set_selected_df(key)
    return df


def get_sample_df():
    """Returns a sample df and makes it the selected df"""
    df = get_redis_df('df_sample')
    if df is None:
        df = pd.DataFrame({
            'A': 1.,
            'B': pd.Timestamp('20130102'),
            'C': pd.Series(1, index=list(range(4)), dtype='float32'),
            'D': [3] * 4,
            'E': pd.Categorical(["test", "train", "test", "train"]),
            'F': 'foo'
        })
        add_redis_df('df_sample', df)
    return df


def save_uploaded_csv(file):
    """Saves a csv on the server, returns the save's destination"""
    save_path = os.path.abspath(app.config[UPLOAD_FOLDER])
    os.makedirs(save_path, exist_ok=True)
    save_as = os.path.join(save_path, file.filename)
    file.save(save_as)
    return save_as


def load_df_from_path(path):
    """Reads a df from a given path to a CSV file"""
    filename = os.path.basename(path)

    df = get_redis_df(filename)
    if df is None:
        df = pd.read_csv(path)
        add_redis_df(filename, df)
    return df


def df_from_request(f):
    filename = f.filename
    f_bytes = f.read()
    f.close()

    df = get_redis_df(filename)
    if df is None:
        try: # utf-8
            df = pd.read_csv(BytesIO(f_bytes))
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(BytesIO(f_bytes), encoding='latin1')
            except UnicodeDecodeError:
                df = pd.read_csv(BytesIO(f_bytes), encoding='cp1252')

        add_redis_df(filename, df)
    return df


def operations(operation):
    df = get_redis_df(get_selected_df_key())
    if df is not None:
        if operation == 'All':
            df = df
        elif operation == 'Stats':
            df = df.describe()
        elif operation == 'Head':
            df = df.head()
        elif operation == 'Tail':
            df = df.tail()
    return df


def select_different_df(key):
    df = get_redis_df(key)
    set_selected_df(key)
    return df


def clear_df_display(command):
    if command == 'all':
        delete_redis_dfs()
    df = None
    return df


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html', df_keys=get_all_df_keys_deserialized())


def prep_df_for_html(df):
    if df is not None:
        df = df.iloc[:50]
        df = df.to_html()
    return df


@app.route('/display_df')
def display_df():
    df = None

    command = request.args.get('command')
    command = make_df_key(command)
    print(f"display_df() command {command}")

    if command=="df_sample":
        print('Loading df_sample.')
        df = get_sample_df()
        set_selected_df(command)
    else:
        df = get_and_select_df(command)
    
    df = prep_df_for_html(df)
    if df is None:
        return ""

    return df


@app.route('/upload_df', methods=['POST'])
def upload_df():
    df = None
    try:
        file = request.files['upload_df']

        print(f"Uploading file {file.filename}.")
        df = df_from_request(file)
    except:
        print("Couldn't upload file {file.filename}.")

    return prep_df_for_html(df)


@app.route('/operate_df')
def operate_df():
    print(get_selected_df_key())
    command = request.args.get('command')
    print(f'Operation recieved: {command}.')
    df = operations(command)
    df = prep_df_for_html(df)
    return df


@app.route('/clear_df_cache')
def clear_df_cache():
    print('Clearing view.')
    command = request.args.get('command')
    df = clear_df_display(command)
    df = prep_df_for_html(df)
    if df is None:
        return ""
    return df


@app.route('/loaded_dfs')
def get_loaded_dfs():
    """Returns a list of dfs from redis in an html <ul>"""
    keys = get_all_df_keys_deserialized()
    if keys == None:
        return ""
    string = "<ul>"
    for key in get_all_df_keys_deserialized():
        string +=  "<li>"+key+"</li>"
    string += "</ul>"
    return string
