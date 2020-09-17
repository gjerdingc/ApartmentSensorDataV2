# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from datetime import timedelta
from datetime import datetime
import requests


#Prometheus timeseries database
db_url = "http://localhost:9090/api/v1"


def dbRangeQuery(query, startTime, endTime, step):
    #Had to run the data through an if condition because some values in prometheus database are incorrect. 
    #For example, temperature in the living room does not change 5 degrees C in 1 minute
    #and then back again the next minute. Not sure why my DHT22 sensor does this.
    #It makes graphs look weird !
    #Returns a pandas DataFrame
    queryString = f"{db_url}/query_range?query={query}&start={startTime}&end={endTime}&step={step}s"
    r = requests.get(queryString)
    data = r.json()

    metric_list=[]
    compare = None

    for i in data['data']['result'][0]['values']:
        i[1] = float(i[1])

        if compare is None:
            compare = i[1]
        elif compare != None and i[1] < 1.4*compare and i[1] > compare/1.4:
            metric_list.append({'time': i[0], 'value': float(i[1])})

    df = pd.DataFrame(metric_list)
    df['time'] = pd.to_datetime(round(df['time']), unit='s')
    df.index = df['time']

    return df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


endTime = datetime.timestamp(datetime.now())
startTime = datetime.timestamp(datetime(2020,7,2))
delta = datetime.now() - datetime(2020,7,2)

#Utregning av laveste lovlige step. Max antall datapunkter for en query i Prometheus er 11000
step = round((86400 * (delta.days + 2))/11000)

df_temp = dbRangeQuery('Temperature', startTime, endTime, step)
df_humi = dbRangeQuery('Humidity', startTime, endTime, step)

fig_temp = px.line(df_temp, x="time", y="value", title='Temperatur i stue')
fig_humi = px.line(df_humi, x="time", y="value", title='Fuktighet i stua')


app.layout = html.Div([
    dcc.Graph(
        id='temp-in-livingroom',
        figure=fig_temp
    ),
        dcc.Graph(
        id='humidity-in-livingroom',
        figure=fig_humi
    )
])

if __name__ == '__main__':
    app.run_server(debug=True, host='10.0.0.39')



