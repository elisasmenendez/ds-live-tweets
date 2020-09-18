import os
import psycopg2

import datetime
import settings
import pandas as pd
import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.express as px 
import plotly.graph_objs as go

app = dash.Dash(__name__)
server = app.server 

app.layout = html.Div(
    style={
        'backgroundColor': '#111111',
        'position':'fixed',
        'width':'100%',
        'height':'100%',
        'top':'0px',
        'left':'0px',
        'z-index':'1000'
    }, 
    children=[   
        html.H2(
            "A Fazenda 12", 
            style={
                'text-align': 'center',
                'color': '#ffffff'
            }),
        dcc.Graph(id='live-graph-bar', animate=True),
        dcc.Interval(
            id='graph-update',
            interval=5000
        ),
    ]
)

@app.callback(Output('live-graph-bar', 'figure'),
              [Input('graph-update', 'n_intervals')])
def update_graph_bar(n):
    
    # Getting the data from our database and reading as a dataframe
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

    df = pd.read_sql('''
    SELECT topic as "Participante", 
        CASE 
            WHEN sentiment = 0 THEN 'Neutro'
            WHEN sentiment = 1 THEN 'Positivo'
            WHEN sentiment = -1 THEN 'Negativo'
        END as "Sentimento", 
        count(*) as "Quantidade"
    FROM (select * from {} order by time desc limit 100) as tweets
    WHERE topic != 'Geral' 
    GROUP BY topic, sentiment
    ORDER BY "Participante"
    '''.format(settings.TABLE_NAME), conn)

    print(df)

    fig_bar = px.bar(
        df, 
        x="Participante", 
        y="Quantidade", 
        color="Sentimento", 
        title="Sentimento dos Tweets",
        template='plotly_dark',
        color_discrete_map={'Neutro':'#BAB0AC','Positivo':'#17BECF','Negativo':'crimson'}
    )
    return fig_bar

if __name__ == '__main__':
    app.run_server(debug=True)