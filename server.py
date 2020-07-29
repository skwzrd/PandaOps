import os
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, session, url_for
from cache import Cache
import json

# TODO
# ====
# filter by column values
# show/hide column dtypes
# convert column dtypes
# apply methods on dfs
# create/remove columns
# plot df's
# save plots
# save modified df's
# hide/show left menu
# solve bug that hide Select button after a while


# DONE
# ====
# check for duplicate records
# refactor code into appropriate modules
# load more rows when scrolling down with "All" selected
# show number of loaded dfs
# replace df list dropdown with <ul>
# convert post requests to ajax
# rearrange buttons
# do not store df's in sessions (there is 4092 byte limit) - find something else
# clean up home()
# css styling (good enough for now)


app = Flask(__name__, static_url_path='/static')

c = Cache()


app.config.update(
    ALLOWED_FILETYPES={'.csv'},
    SECRET_KEY=os.urandom(24).hex(),
    UPLOAD_FOLDER='static/temp',
    SESSION_COOKIE_SAMESITE='Lax'
)

# How many df rows do you want rendered per request
ROW_CHUNK = 10


def save_uploaded_csv(file):
    """Saves a csv on the server, returns the save's destination"""
    save_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
    os.makedirs(save_path, exist_ok=True)
    save_as = os.path.join(save_path, file.filename)
    file.save(save_as)
    return save_as


def load_df_from_path(path):
    """Reads a df from a given path to a CSV file"""
    filename = os.path.basename(path)

    df = c.get_redis_df(filename)
    if df is None:
        df = pd.read_csv(path)
        c.add_redis_df(filename, df)
    return df


def df_from_request(f):
    """Given a request.files object, return its df"""
    filename = f.filename
    f_bytes = f.read()
    f.close()

    df = c.get_redis_df(filename)
    if df is None:
        try: # utf-8
            df = pd.read_csv(BytesIO(f_bytes))
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(BytesIO(f_bytes), encoding='latin1')
            except UnicodeDecodeError:
                df = pd.read_csv(BytesIO(f_bytes), encoding='cp1252')

        c.add_redis_df(filename, df)
    return df


def operations(operation):
    """Perform operations on the selected df and return the product"""
    df = c.get_redis_df(c.get_selected_df_key())
    if df is not None:
        session['display_all'] = False
        if operation == 'All':
            session['display_all'] = True
            session['rows_rendered'] = ROW_CHUNK
            df = df
        elif operation == 'Stats':
            df = df.describe()
        elif operation == 'Head':
            df = df.head()
        elif operation == 'Tail':
            df = df.tail()
    return df


def clear_df_display(command):
    """Given a command, may clear dfs in cache,
        but always clears df display"""
    if command == 'all':
        c.delete_redis_dfs()
        keys = session.keys()
        for k in keys:
            if k.startswith('df_'):
                print(f'Deleting df from session: {k}')
                session[k] = {}
    df = None
    return df


def prep_df_for_html(df, min_chunk=0, max_chunk=ROW_CHUNK, **kwargs):
    """Turns dfs into chunked html tables"""
    if df is not None:
        df = df.iloc[min_chunk: max_chunk]
        df = df.to_html(**kwargs)
    return df


def set_initial_session():
    session['display_all'] = True
    session['rows_rendered'] = ROW_CHUNK


def update_df_meta_in_session(df):
    """Adds df metadata to flask session for use in left menu"""
    selected_df = c.get_selected_df_key()
    d = {}
    d['length'] = len(df.index)
    d['duplicates'] = any(df.duplicated())

    session[selected_df] = d


def print_session():
    print('\nStart Session:')
    for k, v in session.items():
        print(f'{k}: {v}')
    print('End Session\n')


#           ()===========()           #
#           || ENDPOINTS ||           #
#           ()===========()           #


@app.route('/', methods=['GET', 'POST'])
def home():
    """The entry into our SPA"""
    set_initial_session()
    df = prep_df_for_html(c.get_selected_df())
    return render_template(
        'home.html',
        df_keys=c.get_all_df_keys_d(),
        df_key=c.get_selected_df_key_d(),
        df=df,
        filters=False,
        duplicates=False
    )


@app.route('/display_df')
def display_df():
    """Given a GET field with the value of a df key,
        return the html df linked to the df key"""
    df = None

    command = request.args.get('command')
    command = c.make_df_key(command)
    print(f"display_df() command {command}")

    if command=="df_Sample":
        print('Loading df_Sample.')
        df = c.get_sample_df()
        c.set_selected_df(command)
        session['rows_rendered'] = ROW_CHUNK
    else:
        df = c.get_and_select_df(command)
    
    if df is None:
        return ""
    
    update_df_meta_in_session(df)
    print_session()
    df = prep_df_for_html(df)

    return df


@app.route('/left_menu_data')
def get_left_menu_data():
    df = c.get_selected_df()
    d = {}
    d['duplicates'] = any(df.duplicated())
    return json.dumps(d)


@app.route('/upload_df', methods=['POST'])
def upload_df():
    """Handles the upload of a file.
        If file can be read into a df properly, returns an html df"""
    df = None
    try:
        file = request.files['upload_df']

        print(f"Uploading file {file.filename}")
        df = df_from_request(file)
        session['rows_rendered'] = ROW_CHUNK
    except:
        print("Couldn't upload file {file.filename}")

    return prep_df_for_html(df)


@app.route('/operate_df')
def operate_df():
    """Handles the df operations through commands
        it recieves by get requests"""
    print(c.get_selected_df_key())
    command = request.args.get('command')
    print(f'Operation recieved: {command}')
    df = operations(command)
    df = prep_df_for_html(df)
    return df


@app.route('/clear_df_cache')
def clear_df_cache():
    """Handles the clearing of redis keys"""
    print('Clearing view.')
    command = request.args.get('command')
    df = clear_df_display(command)
    df = prep_df_for_html(df)
    if df is None:
        return ""
    return df


@app.route('/selected_df')
def get_selected_df():
    """Returns the selected df's key, deserialized"""
    return c.get_selected_df_key_d()


@app.route('/loaded_dfs')
def get_loaded_dfs():
    """Returns a list of df keys from redis"""
    keys = c.get_all_df_keys_d()
    return json.dumps(keys)


@app.route('/check_df_rows')
def check_df_rows():
    """Checks if more df rows can be loaded.
        If so, returns more rows to be appended to displaying df."""
    selected_df = c.get_selected_df_key()
    df = c.get_redis_df(selected_df)
    update_df_meta_in_session(df)

    if selected_df in session.keys():
        d = {
            'loading_complete': False,
            'rows': None,
            'display_all': session['display_all']
        }
        if session['rows_rendered'] < session[selected_df]['length']:
            # send more rows to be rendered
            df = df.iloc[session['rows_rendered']: session['rows_rendered'] + ROW_CHUNK]
            df = prep_df_for_html(df, header=False)
            d['rows'] = df
            session['rows_rendered'] += ROW_CHUNK
        else:
            d['loading_complete'] = True
        return json.dumps(d)
    else:
        msg = f"Selected df, {selected_df}, has no metadata in session yet. Here are the keys in the session {str(session.keys())}"
        raise KeyError(msg)
