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
# replace df list dropdown with <ul>
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
# rearrange buttons
# do not store df's in sessions (there is 4092 byte limit) - find something else
# clean up home()
# css styling (good enough for now)



def make_df_key(key):
    if key.startswith('df_'):
        return key
    return'df_'+key

def get_session_df(key):
    key = make_df_key(key)
    if session_key_exists(key):
        df = r_context.deserialize(r.get(key))
        return df
    return None


def set_session_df(key, df):
    key = make_df_key(key)
    r.set(key, r_context.serialize(df).to_buffer().to_pybytes())
    change_selected_df_key(key)


def clear_session_dfs():
    for key in get_df_keys():
        print(f'Deleting df from cache: {key}.')
        r.delete(key)


def get_df_keys():
    return [key.decode() for key in r.keys(pattern='df_*')]


def decode_keys(keys):
    return [key.lstrip('df_') for key in keys]


def get_ordered_df_keys():
    """Returns list of df keys (names) from the session with the selected df at index 0."""
    df_keys = get_df_keys()
    selected_df = get_selected_df_key()

    if len(df_keys) == 0:
        return None

    if len(df_keys) > 1:
        for x in df_keys:
            if x == selected_df:
                df_keys.remove(x)
        df_keys = [selected_df] + df_keys

    return decode_keys(df_keys)


def session_key_exists(key):
    if r.exists(key):
        return True
    return False


def change_selected_df_key(key):
    r.set('selected_df', key)


def get_selected_df_key():
    key = r.get('selected_df')
    if key:
        key = make_df_key(key.decode())
    return key


def get_sample_df():
    df = get_session_df('Sample DF')
    if df is None:
        df = pd.DataFrame({
            'A': 1.,
            'B': pd.Timestamp('20130102'),
            'C': pd.Series(1, index=list(range(4)), dtype='float32'),
            'D': [3] * 4,
            'E': pd.Categorical(["test", "train", "test", "train"]),
            'F': 'foo'
        })
        set_session_df('Sample DF', df)
    return df


def save_uploaded_csv(file):
    save_path = os.path.abspath(app.config[UPLOAD_FOLDER])
    os.makedirs(save_path, exist_ok=True)
    save_as = os.path.join(save_path, file.filename)
    file.save(save_as)
    return save_as


def load_df_from_path(path):
    filename = os.path.basename(path)

    df = get_session_df(filename)
    if df is None:
        df = pd.read_csv(path)
        set_session_df(filename, df)
    return df


def df_from_request(f):
    filename = f.filename
    f_bytes = f.read()
    f.close()

    df = get_session_df(filename)
    if df is None:
        df = pd.read_csv(BytesIO(f_bytes))
        set_session_df(filename, df)
    return df


def operations(operation):
    df = get_session_df(get_selected_df_key())
    if df is not None:
        if operation == 'All':
            df = df
        elif operation == 'Describe':
            df = df.describe()
        elif operation == 'Head':
            df = df.head()
        elif operation == 'Tail':
            df = df.tail()
    return df


def select_different_df(key):
    df = get_session_df(key)
    change_selected_df_key(key)
    return df


def clear_df_display(command):
    if command == 'Clear DF Cache':
        clear_session_dfs()
    df = None
    return df


@app.route('/', methods=['GET', 'POST'])
def home():
    df = None
    if request.method == 'POST':
        
        if ('upload_df' in request.files) and (request.files['upload_df']):
            print(f"Uploading file {request.files['upload_df'].filename}.")
            df = df_from_request(request.files['upload_df'])

        elif ('sample_df' in request.form):
            print('Loading sample df.')
            df = get_sample_df()

        elif ('clear' in request.form):
            print('Clearing view.')
            df = clear_df_display(request.form['clear'])

        elif ('operate' in request.form):
            print('Operation recieved.')
            df = operations(request.form['operate'])
        
        elif ('df_selection' in request.form):
            print('Selecting different df.')
            df = select_different_df(request.form['df_selection'])

    if df is not None:
        df = df.to_html()

    return render_template('home.html', df=df, df_keys=get_ordered_df_keys())
