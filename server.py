import os
import pandas as pd
from flask import Flask, render_template, request, url_for, session

app = Flask(__name__, static_url_path='/static')

UPLOAD_FOLDER = 'UPLOAD_FOLDER'
ALLOWED_FILETYPES = {'.csv'}
app.config[UPLOAD_FOLDER] = 'static/temp'
app.config['SECRET_KEY'] = '123456'

DATABASE = 'db/img_board.db'
SCHEMA = 'db/schema.sql'

# TODO
# ====
# do not store df's in sessions (there is a small size limit) - find something else
# clean up home()
# refactor code into appropriate modules
# show/hide column dtypes
# convert column dtypes
# apply methods on df column
# create/remove column
# plot df
# save 
# css (tailwind?)


def get_session_df(key):
    if key in session['dfs'].keys():
        print(f'\'{key}\' found in session\'s df\'s.')
        return pd.read_json(session['dfs'][key])
    print(f'\'{key}\' not found in session\'s df\'s.')
    return None


def set_session_df(key, df):
    session['dfs'][key] = df.to_json()
    change_selected_df_key(key)
    session.modified = True


def clear_session_dfs():
    session['dfs'] = {}


def change_selected_df_key(key):
    session['selected_df'] = key
    session.modified = True


def get_selected_df_key():
    return session['selected_df']


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
        print('Added new sample df to session.')
    else:
        print('Loaded sample df from session.')
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


def operations(operation):
    print(operation)
    df = get_session_df(get_selected_df_key())
    if df is not None:
        if operation == 'All':
            df = df
        elif operation == 'Describe':
            df = df.describe()
        elif operation == 'Top 50':
            df = df.iloc[:50]
        elif operation == 'Head':
            df = df.head()

    return df


def clear_df_display(command):
    if command == 'Clear View':
        print('Clearing view.')

    elif command == 'Clear DF Cache':
        print('Clearing df\'s in session.')
        clear_session_dfs()


def get_df_keys():
    """Returns list of df keys (names) from the session with the selected df at index 0."""
    df_keys = list(session['dfs'].keys())

    if len(df_keys) == 0:
        return None

    elif len(df_keys) == 1:
        return df_keys

    else:
        for x in df_keys:
            if x == session['selected_df']:
                df_keys.remove(x)

        df_keys = [session['selected_df']] + df_keys

    return df_keys


def initialize_session():
    session['dfs'] = {}
    session['selected_df'] = None
    session.modified = True


@app.route('/', methods=['GET', 'POST'])
def home():
    if 'dfs' not in session.keys():
        print('Initializing session df\'s.')
        initialize_session()

    df = None
    if request.method == 'POST':
        
        if ('get_df' in request.files) and (request.files['get_df']):
            print(f"Uploading file \'{request.files['get_df']}\'.")
            path = save_uploaded_csv(request.files['get_df'])
            df = load_df_from_path(path)

        elif ('get_df' in request.form) and(request.form['get_df'] == 'Load Sample DF'):
            print('Loading sample df.')
            df = get_sample_df()

        elif ('clear' in request.form):
            clear_df_display(request.form['clear'])
            df = None

        elif ('operate' in request.form):
            print('Performing operation.')
            df = operations(request.form['operate'])
        
        elif ('df_selection' in request.form):
            print('Switching df based on form selection.')
            df = get_session_df(request.form['df_selection'])
            change_selected_df_key(request.form['df_selection'])

    if df is not None:
        df = df.to_html()

    return render_template('home.html', df=df, df_keys=get_df_keys())

