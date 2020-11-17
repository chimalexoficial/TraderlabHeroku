import pandas as pd
import plotly.express as px
import datetime

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

import json
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
from dash.dependencies import Output, Input
import string
import numpy as np

from dash.dependencies import Input, Output, State, MATCH

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, external_stylesheets])
server = app.server

# Urls
url = "https://www.banxico.org.mx/tipcamb/llenarTasasInteresAction.do?idioma=sp"
url1 = "https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=8&accion=consultarCuadro&idCuadro=CP151&locale=es"
fondos = ["https://www.morningstar.com.mx/mx/funds/snapshot/snapshot.aspx?id=F00000LVWR&tab=1",
          "https://www.bbvaassetmanagement.com/am/am/mx/me/personas/fondos-inversion/ficha/MX52BB0G0051/bbvasia-p-%7C-renta-variable-de-paises-en-asia-y-oceania"]
# Crear agente falso
ua = UserAgent()
header = {"User-Agent": str(ua.chrome)}

# Options
options = [{"label": l, "value": d} for l, d in zip(["6 Meses", "12 Meses", "18 Meses", "24 Meses", "30 Meses",
                                                     "36 Meses", "42 Meses", "48 Meses", "54 Meses", "60 Meses"],
                                                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])]
options1 = [{"label": l, "value": d} for l, d in zip(["$" + str(i * 1000) + ".00 Pesos." for i in range(20, 101, 10)],
                                                     [i * 1000 for i in range(20, 101, 10)])]

# Obtener Actualización de Tasas
# Renta Fija
page = requests.get(url, headers=header)
soup = BeautifulSoup(page.content, "html5lib")
# Renta Variable
page1 = requests.get(fondos[0], headers=header)
soup1 = BeautifulSoup(page1.content, "html5lib")
# Renta Variable Externa
page2 = requests.get(fondos[1], headers=header)
soup2 = BeautifulSoup(page2.content, "html5lib")
# Inflación
page3 = requests.get(url1, headers=header)
soup3 = BeautifulSoup(page3.content, "html5lib")

# Extrayendo Datos
cete28 = float(soup.find(id="CA0_DATO").get_text().strip())
cetes91 = float(soup.find(id="CA1_DATO").get_text().strip())
cete180 = float(soup.find(id="CA2_DATO").get_text().strip())
cete360 = float(soup.find(id="CA3_DATO").get_text().strip())
Bono5 = float(soup.find(id="CA4_DATO").get_text().strip())
Udibono = float(soup.find(id="CA4_DATO").get_text().strip())
inflacion = float("".join(
    [l for l in soup3.find_all(attrs={"class": "cd_tabla_renglon tdObservacion paddingr"})[8].get_text() if
     l in str(string.digits) + "."]))
GBMCRE_BO = float(soup1.find(attrs={"class": "col9 value number"}).get_text())
BBVASIA = 10.61  # "".join([l for l in soup2.find(attrs = {"class":"green"}).get_text().replace("\t","").replace("\n", "").split("parseFloat(")[1][:5] if l in str(string.digits)+"."])
briq = 16
finestra = 10.25
Trader = 25


# Funcioón Rendimientos
def crecimiento(Monto, Plazo):
    comparativas = json.loads(open("Tasas a Comparar.json", "r").read())
    rendimientos = []
    rendimientos.append([((1 + (float(cete28) / 100) / 12) ** (i + 1)) * Monto for i in range(6 * Plazo)])
    rendimientos.append([((1 + (float(cetes91) / 100) / 4) ** (i + 1)) * Monto for i in range(2 * Plazo)])
    rendimientos.append([((1 + (float(cete180) / 100) / 2) ** (i + 1)) * Monto for i in range(Plazo)])
    rendimientos.append([Monto + (Monto / 2) * (float(cete360) / 100) * (i + 1) for i in range(Plazo)])
    rendimientos.append([Monto + (Monto / 2) * float(Bono5) / 100 * (i + 1) for i in range(Plazo)])
    rendimientos.append([Monto + (Monto / 2) * float(Udibono) / 100 * (i + 1) for i in range(Plazo)])
    rendimientos.append([Monto + (Monto / 2) * float(GBMCRE_BO) / 100 * (i + 1) for i in range(Plazo)])
    rendimientos.append([Monto + (Monto / 2) * float(BBVASIA) / 100 * (i + 1) for i in range(Plazo)])
    rendimientos.append([Monto + (Monto / 2) * float(briq) / 100 * (i + 1) for i in range(Plazo)])
    rendimientos.append([Monto + (Monto / 2) * float(finestra) / 100 * (i + 1) for i in range(Plazo)])
    rendimientos.append([Monto - (Monto / 2) * float(inflacion) / 100 * (i + 1) for i in range(Plazo)])
    rendimientos.append([Monto + (Monto / 2) * float(Trader) / 100 * (i + 1) for i in range(Plazo)])

    return rendimientos


# Correr Función
rends = crecimiento(1000, 1)
[l.insert(0, 1000) for l in rends]

# Graficar

meses = [["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
          "Octubre", "Noviembre", "Diciembre"]] * int((len(rends[2]) - 2)) if int((len(rends[2]) - 2)) > 0 else [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
if len(meses) > 6:
    s = np.concatenate(
        [[l + " " + str(s) for l in meses[s - 2020]] for s in range(2020, 2020 + int((len(rends[2]) - 2)))]).tolist()
    s.insert(1000, "Final")
else:
    s = meses
    s.insert(1000, "Final")

trace0 = go.Scatter(x=[i for i in range(len(rends[0]))], y=rends[0],
                    mode="markers+lines", name="Cetes 28 Días")
trace1 = go.Scatter(x=[i * 3 for i in range(len(rends[1]))], y=rends[1], mode="markers+lines", name="Cetes 91 Días")
trace2 = go.Scatter(x=[i * 6 for i in range(len(rends[2]))], y=rends[2], mode="markers+lines", name="Cetes 180 Días")
trace3 = go.Scatter(x=[i * 6 for i in range(len(rends[3]))], y=rends[3], mode="markers+lines", name="Cetes 360 Días")
trace4 = go.Scatter(x=[i * 6 for i in range(len(rends[4]))], y=rends[4], mode="markers+lines", name="Bono a 5 Años")
trace5 = go.Scatter(x=[i * 6 for i in range(len(rends[5]))], y=rends[5], mode="markers+lines", name="Udibono")
trace6 = go.Scatter(x=[i * 6 for i in range(len(rends[6]))], y=rends[6], mode="markers+lines", name="GBMCRE BO")
trace7 = go.Scatter(x=[i * 6 for i in range(len(rends[7]))], y=rends[7], mode="markers+lines", name="BBVASIA")
trace8 = go.Scatter(x=[i * 6 for i in range(len(rends[8]))], y=rends[8], mode="markers+lines", name="Briq")
trace9 = go.Scatter(x=[i * 6 for i in range(len(rends[9]))], y=rends[9], mode="markers+lines", name="Finestra")
trace10 = go.Scatter(x=[i * 6 for i in range(len(rends[10]))], y=rends[10], mode="markers+lines", name="Inflación")
trace11 = go.Scatter(x=[i * 6 for i in range(len(rends[11]))], y=rends[11], mode="markers+lines", line=dict(width=4),
                     name="Trader")

data = [trace0, trace1, trace2, trace3, trace4, trace5, trace6,
        trace7, trace8, trace9, trace10, trace11]

# Data inicial
capital_inicial = 1000
capital_meta = 2000
capital_actual = 0

app.layout = html.Div([
    # Barra de Navegación
    dbc.NavbarSimple(
        children=[
            # Boton subir archivo CSV
            dbc.NavItem(html.Div([
        dcc.Input(id='username', value='Ingresa la URL...', type='text'),
        html.Button(id='submit-button', type='submit', children='Subir archivo'),
        html.Div(id='output_div')
    ])),
            # Lista de submenu
            dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem("Análisis", header=True),
                    dbc.DropdownMenuItem("Análisis de gráficos", href="https://tradingview.com"),
                    dbc.DropdownMenuItem("Noticias económicas", href="https://mx.investing.com/news/latest-news"),
                ],
                nav=True,
                in_navbar=True,
                label="Herramientas",
                style={'text-align': 'center', 'margin': '0px'}
            ),
        ],
        brand="Sube tu archivo ->",
        brand_href="#",
        color="primary",
        dark=True,
        style={'height': '50px', 'text-align': 'center', 'margin-bottom': '10px', 'padding': '10px'}
    ),

    dbc.Row([
        dbc.Col(html.H2("Trader Lab 1.0", style={'font-family': 'Lucida Bright'}), width=12,
                style={'text-align': 'center', 'margin': '10px'})
    ]),

    # Filtros
    dbc.Row([
        dbc.Col([
            html.H5(children='Año: ', style={'text-align': 'center', 'padding': '3px'})
        ], width={'size': 1}),
        dbc.Col([
            dcc.Dropdown(id='select_year',
                         options=[
                             {'label': '2019', 'value': 2019}
                         ],
                         multi=False,
                         value=2019,
                         style={'width': '100%'}
                         )
        ], width={'size': 1}),
        dbc.Col([
            html.H5(children='Resultado: ', style={'text-align': 'center', 'padding': '3px'})
        ], width={'size': 1}),
        dbc.Col([
            dcc.Dropdown(id='exito',
                         options=[
                             {'label': 'Todos', 'value': 'All'},
                             {'label': 'Exitosas', 'value': 'Good'},
                             {'label': 'Perdidas', 'value': 'Bad'}
                         ],
                         multi=False,
                         value='All',
                         style={'width': '100%'}
                         )
        ], width={'size': 1}),
        dbc.Col(
            html.H5(children='Divisas: ', style={'text-align': 'center', 'padding': '3px'}),
            width={'size': 1}
        ),
        dbc.Col(
            dcc.Dropdown(id='divisa',
                         options=[
                             {'label': 'EURUSD', 'value': 'EURUSD'},
                             {'label': 'XAUUSD', 'value': 'XAUUSD'},
                             {'label': 'GBPUSD', 'value': 'GBPUSD'},
                             {'label': 'EURJPY', 'value': 'EURJPY'},
                             {'label': 'USDCAD', 'value': 'USDCAD'},
                             {'label': 'USDJPY', 'value': 'USDJPY'},
                             {'label': 'SUDMXN', 'value': 'SUDMXN'},
                             {'label': 'GBPJPY', 'value': 'GBPJPY'},
                             {'label': 'AUDUSD', 'value': 'AUDUSD'},
                             {'label': 'BTCUSD', 'value': 'BTCUSD'},
                             {'label': 'EURGBP', 'value': 'EURGBP'}
                         ],
                         multi=True,
                         value=['EURUSD', 'XAUUSD', 'GBPUSD', 'EURJPY', 'USDCAD', 'USDJPY', 'SUDMXN', 'GBPJPY',
                                'AUDUSD', 'BTCUSD', 'EURGBP'],
                         style={'width': '100%'}
                         ),
            width={'size': 6},
        ),
        dbc.Col([
            dbc.Button("Abrir Tabla", id="open", style={'margin-left': '5px'}),
            dbc.Modal(
                [
                    dbc.ModalHeader("Tabla de operaciones"),
                    dbc.ModalBody(
                        html.Div(dcc.Graph(id='fig'))
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close", className="ml-auto")
                    ),
                ],
                id="modal",
                size="xl"
            )
        ], width={'size': 1}),
    ], no_gutters=True),

    # Indicadores
    dbc.Row([
        dbc.Col(dbc.Card(
            dbc.CardBody(
                [
                    html.H4(f'${capital_inicial} USD', className="card-title"),
                    html.H6('Capital inicial', className="card-subtitle"),
                ],
            ), color="light"
        ), width=3),
        dbc.Col(dbc.Card(
            dbc.CardBody(
                [
                    html.H4(f'${capital_meta} USD', className="card-title"),
                    html.H6('Capital meta', className="card-subtitle"),
                ],
            ), color="light"
        ), width=3),

        dbc.Col(dbc.Card(
            dbc.CardBody(
                [
                    html.H4(id='capital_actual_h', className="card-title"),
                    html.H6('Capital actual', className="card-subtitle"),
                ],
            )
            , color="light"
        ), width=3),

        dbc.Col(dbc.Card(
            dbc.CardBody(
                [
                    html.H4(id='factor_de_ganancia_h', className="card-title"),
                    html.H6('Retorno de Inversion', className="card-subtitle"),
                ],
            )
            , color="light"
        ), width=3),
    ], style={'margin': '10px'}),

    # Pestañas
    html.Div([
        dcc.Tabs([
            dcc.Tab(label='Curva de capital', children=[
                dbc.Row([
                    dbc.Col(html.H5(
                        'El gráfico muestra el aumento o la disminución del capital en el tiempo con base en los resultados de las operaciones realizadas.'),
                        style={'margin': '20px'}),
                ]),
                dcc.Graph(id='capital')
            ]),
            dcc.Tab(label='Efectividad por par de divisa', children=[
                dbc.Row([dbc.Col(
                html.H5("El gráfico muestra la efectividad de  las operaciones realizadas de cada par de divisa."),
                style={'margin': '20px'})]),
                dcc.Graph(id='efectividad')
            ]),
                dcc.Tab(label='Efectividad de Operaciones', children=[
                    dbc.Row([dbc.Col(html.H5(
                        "El gráfico muestra la efectividad de las operaciones con el porcentaje de operaciones ganadas y operaciones perdidas."),
                        style={'margin': '20px'})]),
                    dcc.Graph(id='aciertos')
            ]),
            dcc.Tab(label='Logro vs Meta', children=[
                dbc.Row(dbc.Col(html.H5('El gráfico muestra el capital actual alcanzado de la meta deseada'),
                                style={'margin': '20px'})),
                dcc.Graph(id='goal')
            ]),
            dcc.Tab(label='Distribución de las Operaciones', children=[
                dbc.Row(dbc.Col(html.H5(
                    "El gráfico muestra la distribución de las operaciones realizadas por cada par de divisa en porcentaje."),
                    style={'margin': '20px'})),
                dcc.Graph(id='figPie')
            ]),
            dcc.Tab(label='Benchmark', children=[
                dbc.Row(dbc.Col(html.H5(
                    'El gráfico muestra la comparativa del rendimiento del trader contra otros instrumentos financieros.'),
                    style={'margin': '20px'})),
                dcc.Graph(id='drawdown')
            ])
        ])
    ])
    ,
])


@app.callback(
    Output({'index': MATCH, 'role': 'modal'}, "is_open"),
    [Input({'index': MATCH, 'role': 'open'}, "n_clicks"), Input({'index': MATCH, 'role': 'close'}, "n_clicks")],
    [State({'index': MATCH, 'role': 'modal'}, "is_open")])

@app.callback(
    Output('output_div', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('username', 'value')])

def update_output(clicks, input_value):
    if clicks is not None:
        print(clicks, input_value)

def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open




# Entradas y salidas del callback
@app.callback(
    [
        # Output(component_id = 'OutputContainer', component_property = 'children'),
        Output(component_id='fig', component_property='figure'),
        Output(component_id='figPie', component_property='figure'),
        Output(component_id='capital', component_property='figure'),
        Output(component_id='efectividad', component_property='figure'),
        Output(component_id='goal', component_property='figure'),
        Output(component_id='drawdown', component_property='figure'),
        Output(component_id='aciertos', component_property='figure'),
        # Output(component_id='profitFactor', component_property='figure'),
        # Output(component_id='drawdown', component_property='figure'),
        Output("modal", "is_open"),
        Output(component_id='capital_actual_h', component_property='children'),
        Output(component_id='factor_de_ganancia_h', component_property='children')
    ],
    [
        Input(component_id='select_year', component_property='value'),
        Input(component_id='exito', component_property='value'),
        Input(component_id='divisa', component_property='value'),
        Input("open", "n_clicks"), Input("close", "n_clicks")
    ],
    [State("modal", "is_open")]
)

# Función para callback
def update_graph_modal(select_year, exito, divisa, n1, n2, is_open):
    # Modal
    if n1 or n2:
        is_open = not is_open

    # Work data
    update_output.input_value = 'http://www.sharecsv.com/dl/6b041ed2942e86673c389aa9172a10f4/tradeview2.csv'
    df_original = pd.read_csv(update_output.input_value)
    df = df_original.copy()
    capital_actual = capital_inicial + df['Profit'].sum()

    df['openTime'] = pd.to_datetime(df['openTime'])
    df['closeTime'] = pd.to_datetime(df['closeTime'])
    df['Symbol'] = df['Symbol'].str.upper()
    df['Count'] = 1

    df_filtered = df.copy()
    df_filtered['year'] = pd.DatetimeIndex(df_filtered['closeTime']).year
    df_filtered = df_filtered[df_filtered['year'] == select_year]

    if exito == 'Good':
        df_filtered = df_filtered[df_filtered['Profit'] >= 0]
    elif exito == 'Bad':
        df_filtered = df_filtered[df_filtered['Profit'] < 0]
    elif exito == 'All':
        df_filtered = df_filtered

    df_filtered = df_filtered[df_filtered['Symbol'].isin(divisa)]

    columns_info = ['openTime', 'Type', 'Size', 'Symbol', 'openPrice', 'closeTime', 'closePrice', 'Profit']
    df_table = df_filtered.loc[:, columns_info]
    df_table.sort_values(by=['closeTime'], inplace=True)

    ############# Tabla general
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df_table.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[df_table[columns_info[0]], df_table[columns_info[1]], df_table[columns_info[2]],
                           df_table[columns_info[3]], df_table[columns_info[4]], df_table[columns_info[5]],
                           df_table[columns_info[6]], df_table[columns_info[7]]],
                   fill_color='lavender',
                   align='left'))
    ])
    colors = ['#343434', '#7FB7BE', '#D3F3EE', '#DACC3E', '#BC2C1A', '#D7816A', '#9F7E69', '#F5853F', '#BD4F6C',
              '#8F8389']
    ############# pie chart
    figPie = go.Figure(data=[go.Pie(labels=df_filtered.Symbol, values=df_filtered.Count)])
    figPie.update_traces(hole=.4, hoverinfo="label+percent", marker=dict(colors=colors))

    ############# Curva de Capital
    df_table["Capital"] = df_table["Profit"].cumsum() + capital_inicial
    curva_capital = px.line(
        df_table,
        x="closeTime",
        y="Capital"

        # title='Curva de Capital'
    )
    curva_capital.update_traces(hovertemplate='<i>Capital</i>: $%{y:.2f}')
    curva_capital.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    curva_capital.update_yaxes(gridcolor='LightPink')

    ############# Benchmark / Rendimiento con trader, cetes y banco
    # ORIGINAL rendPorcentualTrader = ((df["Profit"].sum()) / capital_inicial) * 100
    rendPorcentualTrader = ((df["Profit"].sum()) / capital_inicial)
    rendPorcentualCetes = 0.0418
    rendPorcentualBanco = 0.0117

    compArray = ['Cetes', 'Trader', 'Banco']
    figRendimiento = go.Figure(
        data=go.Scatter(x=compArray, y=[rendPorcentualCetes, rendPorcentualTrader, rendPorcentualBanco],
                        hovertemplate="Rendimiento anual del: %{y:.0%}<br>"))
    # figRendimiento.update_layout(title_text='Benchmark')

    ############# Profit Factor
    # (Ganadoras/Perdedoras) -> Superior a 1 OK!! Inferior, mala inversion
    contPositivo = 0
    contNegativo = 0
    for x in df.index:
        val = df['Profit'][x]
        if val < 0:
            contNegativo = contNegativo + 1

        else:
            contPositivo = contPositivo + 1
    # profitFactorVal = contPositivo / contNegativo
    profitFactorVal = (((capital_actual - capital_inicial) / capital_inicial) * 100)
    profitFactorVal = round(profitFactorVal, 2)
    profitFactorVal = f'{profitFactorVal}%'

    # profitFactor = go.Figure(go.Indicator(
    #     mode="gauge+number",
    #     value=profitFactorVal,
    #     title={'text': "Rendimiento del Trader"},
    #     gauge={'axis': {'visible': True, 'range': [0, 2]},
    #            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 1}},

    #     domain={'x': [0, 1], 'y': [0, 1]}
    # ))

    # ############# Drawdown
    # total = df_table["Profit"].cumsum() + capital_inicial
    # minProfit = total.min()
    # maxProfit = total.max()

    # df_table["Capital"] = df_table["Profit"].cumsum() + capital_inicial
    # drawdown = px.line(df_table, x="closeTime", y="Capital")
    # drawdown.update_layout(shapes=[
    #     dict(
    #         type='line',
    #         xref='paper', x0=0, x1=1,
    #         yref='y', y0=minProfit, y1=minProfit,
    #     ),
    #     dict(
    #         type='line',
    #         xref='paper', x0=0, x1=1,
    #         yref='y', y0=maxProfit, y1=maxProfit,
    #     )])

    layout = go.Layout(title="Rendimiento Anualizado",
                       hovermode="closest",
                       xaxis={"title": "Meses del Año",
                              "tickvals": [i for i in range(len(rends[0]))],
                              "ticktext": s},
                       yaxis={"title": "Rendimiento + Capital"})
    drawdown = go.Figure(data=data, layout=layout)
    drawdown.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    drawdown.update_yaxes(gridcolor='LightPink')

    ############# Efectividad de Operaciones
    # Ganadoras/Perdedoras * 100
    operacionesTotales = df.shape[0]
    aciertos = (contPositivo / operacionesTotales) * 100
    perdidas = (100 - aciertos)

    values = [aciertos, perdidas]
    labels = ['Ganadas', 'Perdidas']

    figAciertos = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, textfont={'color': "white"})])
    # figAciertos.update_layout(title_text='Efectividad de Operaciones')

    ############# Efectividad por Par de Divisa
    efect_x = df_filtered['Symbol'].unique()
    efect_y = []
    for x in efect_x:
        df_x = df_filtered[df_filtered['Symbol'] == x]
        positivos = len(df_x[df_x['Profit'] >= 0])
        # ORIGINAL efect_y.append((positivos / len(df_x)) * 100)
        efect_y.append((positivos / len(df_x)) * 100)

    figBar = go.Figure(
        [go.Bar(name='Porcentaje de efectividad', x=efect_x, y=efect_y, hovertemplate="Efectividad del: %{y:.2f}%<br>",
                marker_color=['#343434', '#7FB7BE', '#D3F3EE', '#DACC3E', '#BC2C1A', '#D7816A', '#9F7E69', '#F5853F',
                              '#BD4F6C', '#8F8389'],
                showlegend=False)])

    figBar.update_layout(
        # title_text='Efectividad por Par de Divisa',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', yaxis_title="Porcentaje de efectividad"
    )
    figBar.update_yaxes(gridcolor='LightPink')

    ############# Meta

    limite_capital = ((capital_meta - capital_inicial) * 1.50) + capital_inicial

    goal = go.Figure(go.Indicator(
        mode="gauge+number",
        value=capital_actual,
        number={'prefix': "$", "suffix": " USD"},
        # title={'text': f'Meta: {capital_meta}'},
        # title={'text': 'Logro vs Meta'},
        gauge={'axis': {'visible': True, 'range': [capital_inicial, limite_capital]},
               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': capital_meta}},
        domain={'x': [0, 1], 'y': [0, 1]},
    ))

    ############# Texto Capital Actual
    capital_actual_text = f' ${capital_actual}'

    # return fig, figPie, curva_capital, figBar, goal, figRendimiento, figAciertos, profitFactor, drawdown, is_open
    return fig, figPie, curva_capital, figBar, goal, drawdown, figAciertos, is_open, capital_actual_text, profitFactorVal


# web server
if __name__ == '__main__':
    app.run_server(debug=True)


