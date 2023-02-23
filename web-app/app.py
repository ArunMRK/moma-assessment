from dotenv import load_dotenv
import os
load_dotenv(override=True, verbose=True)
import psycopg2
import psycopg2.extras
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import datetime
import plotly.express as px
import dash_bootstrap_components as dbc
pd.options.plotting.backend = 'plotly'

RDS_DB = os.getenv("DB_NAME")
RDS_USER = os.getenv("DB_USER")
RDS_PASSWORD = os.getenv("DB_PASSWORD")
RDS_HOST = os.getenv("DB_HOST")

def get_db_connection() -> psycopg2.extensions.connection:
    """ Create a connection for database postgres"""
    try:
        conn = psycopg2.connect(f"""
    dbname={RDS_DB}
    user={RDS_USER} 
    password={RDS_PASSWORD}
    host={RDS_HOST}""")
        return conn
    except:
        print("Error connecting to database.")

conn=get_db_connection()
cursor=conn.cursor()

artist_query=pd.read_sql_query(
    '''
    SELECT 
    * FROM
    artist
    ''',
    conn
)

artwork_query=pd.read_sql_query(
    '''
    SELECT 
    * FROM
    artwork
    ''',
    conn
)

artist_df=pd.DataFrame(artist_query, columns=['artist_id','artist_name','nationality','gender','year_start','year_end'])
artwork_df=pd.DataFrame(artwork_query, columns=['artwork_id','title','year_completed','department','artist_id'])
df=pd.merge(artist_df,artwork_df,on='artist_id',how='inner')
df = df[df['title'].str.contains('Untitled')==False ]

px.defaults.template = "ggplot2"


decades = ['2000s', '2010s', '2020s']
decade_bins = [2000,2010,2020,2030]
df['decade'] = pd.cut(df['year_completed'], labels=decades, bins=decade_bins)
df['here'] = 1 #Allows summing up of columns
fig1=px.bar(df,x='nationality',y='here',title='Artist nationality',labels={'nationality': 'Artist nationality',
    'here': 'No. of pieces'},color='nationality')
fig2=px.pie(values=df['here'],names=df['gender'],title='Artist gender')
fig3=px.pie(values=df['here'],names=df['decade'],title='Decade works completed')
fig4=px.pie(values=df['here'],names=df['department'],title='Department work is from')



app = Dash(__name__)
app.layout = dbc.Container([
    dbc.Row([
    dbc.Col(html.H1(children='Museum of Modern Art')),
    ]),
    html.Div([
    html.H4(children= f'There are {df.shape[0]} paintings in the collection in total.')
    ]),
    html.Div([
    html.H3(children='Artists')
    ]),
    dbc.Col([
    dcc.Dropdown(list(df['nationality'].unique()), 'American', id='country-dropdown'),
    html.Div(id='country-output-container')
    ]),
    dbc.Col([
    dcc.Dropdown(['Male','Female','Other/Unknown'], 'Male', id='gender-dropdown'),
    html.Div(id='gender-output-container')
    ]),
    html.Div(children=[
    html.Div(
        dcc.Graph(
            id='country-graph',
           figure=fig1
        ), style={'display': 'inline-block'}),
    html.Div(
        dcc.Graph(
            id='gender-graph',
            figure=fig2
        ), style={'display': 'inline-block'})
    ], style={'width': '100%', 'display': 'inline-block'}),
    html.Div([
    html.H3(children='Artworks')
    ]),
    html.Div(children=[
    html.Div([
    html.H5(children='Year')
    ]),
    html.Div([
    dcc.Dropdown(['This year','Last 5 years','2020s','2010s','2000s'], '2020s', id='decade-dropdown'),
    html.Div(id='decade-output-container')
    ]),
    html.Div([
    html.H5(children='Department')
    ]),
    html.Div([
    dcc.Dropdown(['Drawings & Prints', 'Photography', 'Painting & Sculpture',
 'Media and Performance', 'Architecture & Design'], 'Drawings & Prints', id='dept-dropdown'),
    html.Div(id='dept-output-container')
    ]),
    ]),
    html.Div(children=[
    html.Div(
        dcc.Graph(
            id='decade-graph',
           figure=fig2
        ), style={'display': 'inline-block'}),
    html.Div(
        dcc.Graph(
            id='dept-graph',
            figure=fig4
        ), style={'display': 'inline-block'})
    ], style={'width': '100%', 'display': 'inline-block'}),
])
    

@app.callback(
    Output('country-output-container', 'children'),
    Input('country-dropdown', 'value')
)
def update_output(value):
    country_count=len(df[df['nationality'] == value ])
    return f'There are {country_count} paintings in the collection from {value} artists'

@app.callback(
    Output('gender-output-container', 'children'),
    Input('gender-dropdown', 'value')
)
def update_output(value):
    gender_count=len(df[df['gender'] == value ])
    if value is not None:
        return f'There are {gender_count} paintings in the collection from {value.lower()} artists'
    else:
        nullgender = df['gender'].isna().sum().sum()
        return f'There are {nullgender} paintings in the collection from artists of unknown or non-binary gender'

@app.callback(
    Output('decade-output-container', 'children'),
    Input('decade-dropdown', 'value')
)
def update_output(value):
    today = datetime.datetime.now() 
    current_year = today.strftime("%Y")
    if value == 'This year':
        art_this_year = len(df[df['year_completed'] == (int(current_year)) ])
        return f'There are {art_this_year} paintings in the collection'
    if value == 'Last 5 years':
        art_last_five_years = len(df[df['year_completed'] >= (int(current_year)-5) ])
        return f'There are {art_last_five_years} paintings in the collection from the last five years'
    else:
        decade_count=len(df[df['decade'] == value ])
        return f'There are {decade_count} paintings in the collection from the {value}'

@app.callback(
    Output('dept-output-container', 'children'),
    Input('dept-dropdown', 'value')
)
def update_output(value):
    dept_count=len(df[df['department'] == value ])
    return f'There are {dept_count} paintings in the collection from the {value} department'

if __name__ == '__main__':
    app.run_server(debug=True)