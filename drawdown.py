import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import json
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
from dash.dependencies import Output, Input
import string
import numpy as np

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
layout = go.Layout(title="Rendimiento Anualizado",
                   hovermode="closest",
                   xaxis={"title": "Meses del Año",
                          "tickvals": [i for i in range(len(rends[0]))],
                          "ticktext": s},
                   yaxis={"title": "Rendimiento + Capital"})
fig = go.Figure(data=data, layout=layout)
fig.update_layout(width=2000, height=750, font={"size": 25}, title_x=0.5, plot_bgcolor='rgb(204,236,239)')

# Crear Aplicación

app = dash.Dash()

colors = {"background": "#111111", "text": "#7FDBFF"}

app.layout = html.Div(children=[
    html.Div(children="Comparativa de Inversión", style={"textAlign": "center",
                                                         "fontSize": 100,
                                                         "backgroundColor": "orange",
                                                         "border": "5px black solid"}),
    html.P(),
    html.Div(children=[
        dcc.Dropdown(id="Money",
                     options=options1,
                     value=1000)], style={"display": "inline-block",
                                          "verticalAlign": "top",  # "marginLeft":"140px",
                                          "width": "700px", "fontSize": 25,
                                          "border": "5px black solid",
                                          "textAlign": "center"}),
    html.Div(children=[
        dcc.Dropdown(id="TimeFrame",
                     options=options,
                     value=1)], style={"display": "inline-block",
                                       "verticalAlign": "top",  # "marginLeft":"140px",
                                       "width": "700px",
                                       "border": "5px black solid",
                                       "fontSize": 25, "textAlign": "center"}),

    dcc.Graph(id="Plot", figure=fig)],
    style={"border": "5px black solid"})


@app.callback(Output(component_id="Plot", component_property="figure"),
              [Input(component_id="Money", component_property="value"),
               Input(component_id="TimeFrame", component_property="value")])
def update_graph(Monto, Plazo):
    # Correr Función
    rends = crecimiento(Monto=Monto, Plazo=Plazo)
    [l.insert(0, Monto) for l in rends]

    # Graficar

    meses = [["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
              "Octubre", "Noviembre", "Diciembre"]] * int((len(rends[2]) - 2)) if int((len(rends[2]) - 2)) > 0 else [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]

    if Plazo > 1:
        s = np.concatenate([[l + " " + str(s) for l in meses[s - 2020]] for s in
                            range(2020, 2020 + int((len(rends[2]) - 2)))]).tolist()
        s.insert(1000, "Final")
    else:
        s = meses
        s.insert(1000, "Final")

    trace0 = go.Scatter(x=[i for i in range(len(rends[0]))], y=rends[0],
                        mode="markers+lines", name="Cetes 28 Días")
    trace1 = go.Scatter(x=[i * 3 for i in range(len(rends[1]))], y=rends[1], mode="markers+lines", name="Cetes 91 Días")
    trace2 = go.Scatter(x=[i * 6 for i in range(len(rends[2]))], y=rends[2], mode="markers+lines",
                        name="Cetes 180 Días")
    trace3 = go.Scatter(x=[i * 6 for i in range(len(rends[3]))], y=rends[3], mode="markers+lines",
                        name="Cetes 360 Días")
    trace4 = go.Scatter(x=[i * 6 for i in range(len(rends[4]))], y=rends[4], mode="markers+lines", name="Bono a 5 Años")
    trace5 = go.Scatter(x=[i * 6 for i in range(len(rends[5]))], y=rends[5], mode="markers+lines", name="Udibono")
    trace6 = go.Scatter(x=[i * 6 for i in range(len(rends[6]))], y=rends[6], mode="markers+lines", name="GBMCRE BO")
    trace7 = go.Scatter(x=[i * 6 for i in range(len(rends[7]))], y=rends[7], mode="markers+lines", name="BBVASIA")
    trace8 = go.Scatter(x=[i * 6 for i in range(len(rends[8]))], y=rends[8], mode="markers+lines", name="Briq")
    trace9 = go.Scatter(x=[i * 6 for i in range(len(rends[9]))], y=rends[9], mode="markers+lines", name="Finestra")
    trace10 = go.Scatter(x=[i * 6 for i in range(len(rends[10]))], y=rends[10], mode="markers+lines", name="Inflación")

    data = [trace0, trace1, trace2, trace3, trace4, trace5, trace6,
            trace7, trace8, trace9, trace10, trace11]
    layout = go.Layout(title="Rendimiento Anualizado",
                       hovermode="closest",
                       xaxis={"title": "Meses del Año",
                              "tickvals": [i for i in range(len(rends[0]))],
                              "ticktext": s},
                       yaxis={"title": "Rendimiento + Capital"})
    fig = go.Figure(data=data, layout=layout)
    fig.update_layout(width=2000, height=750, font={"size": 25}, title_x=0.5, plot_bgcolor='rgb(204,236,239)')

    return fig


if __name__ == "__main__":
    app.run_server()