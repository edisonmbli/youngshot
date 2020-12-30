import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_auth

from app import app
from apps import youngshot
from profiles import VALID_USERNAME_PASSWORD_PAIRS

server = app.server
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


def home_page_struc():
    return html.Div([
        html.P('Welcome to Plotly Dash'),
        dcc.Link('年轻人专项热点_投后分析', href='/apps/youngshot')
    ])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        # return home_page_struc()
        return youngshot.layout
    elif pathname == '/apps/youngshot':
        return youngshot.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)
