import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from apps import youngshot

server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


def home_page_struc():
    return html.Div([
        html.P('Welcome to the Auto Dashboard'),
        dcc.Link('goto Demo', href='/apps/app_demo'),
        html.Br(),
        dcc.Link('goto Video Upload Anslysis', href='/apps/youngshot')
    ])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return home_page_struc()
    elif pathname == '/apps/youngshot':
        return youngshot.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)
