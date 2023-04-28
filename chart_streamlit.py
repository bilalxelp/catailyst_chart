from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
from datetime import date, datetime
import re
from yahoofinancials import YahooFinancials
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from plotly.subplots import make_subplots
import streamlit as st


st.set_page_config(layout='wide')

st.title("Visualization of Company Stock and Events")

colors = {
    'background': '#111111',
    'text': '#eeeee4'}

df = pd.read_csv('public_clinical_events.csv')

companies_dict = {}
for x in range(len(df)):
    companies_dict[df['Base Name'][x]] = str(df['Ticker'][x]).upper()
temp = []
company_map = dict()
for key, val in companies_dict.items():
    if val not in temp:
        temp.append(val)
        company_map[key] = val


all_tickers = df['Base Name'].unique().tolist()
all_tickers = [tick.upper() for tick in all_tickers]
company_name = st.selectbox('Select a company:', all_tickers)


start_date = str(st.date_input('Start date'))
end_date = str(st.date_input('End date'))


def generate_chart(company, start, end, display_name):
    prices_df = yf.download(company, start=start, end=end, progress=False)
    prices_df.reset_index(drop=False, inplace=True)
    
    if 'Close' in prices_df.columns:
        print("Price Data Downloaded")
    # print(prices_df)

    df['Ticker'] = df['Ticker'].str.upper()
    new_df = df[df['Ticker'] == company]
    new_df.reset_index(drop=True, inplace=True)

    #filter for events that happened in date range provided
    event = new_df.copy()
    event.set_index('Date', drop=True, inplace=True)
    event.sort_index(inplace=True)
    event = event.loc[start:end]
    
    prices_df['Date'] = pd.to_datetime(prices_df['Date']).dt.date

    prices_df.set_index('Date', inplace=True)
    event.index = pd.DatetimeIndex(event.index)
    
    prices_df.index = prices_df.index.astype('datetime64[ns]')
    
    # print(prices_df)

    chart_df = pd.merge(event, prices_df, on='Date', how='outer')
    chart_df.sort_index(inplace=True)

    chart_df['Tracers'] = ''
    for x in range(len(chart_df)):
        if str(chart_df['Event'].iloc[x]) !='nan':
            
            tracer = {'Event':'', 'Asset':'', 'Event':'', 'Indication':''}
            
            tracer['Event'] = chart_df['Event'].iloc[x]
            tracer['Asset'] = chart_df['Asset Name'].iloc[x]
            tracer['Indication'] = chart_df['Indication'].iloc[x]
            chart_df['Tracers'].iloc[x] = str(tracer)
            chart_df['Tracers'].iloc[x] = chart_df['Tracers'].iloc[x].replace(',', '<br>')

    tracer_df = chart_df.dropna(subset=['Event'])

    chart_df['MA5'] = chart_df.Close.rolling(5).mean()
    chart_df['MA20'] = chart_df.Close.rolling(20).mean()

    # plot the candlesticks
    candlesticks = go.Candlestick(
        x=chart_df.index,
        open=chart_df['Open'],
        high=chart_df['High'],
        low=chart_df['Low'],
        close=chart_df['Close'],
        showlegend=False)

    fig = go.Figure(candlesticks)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(candlesticks, secondary_y=True)

    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df.MA5, line=dict(color='orange', width=1), name='5-Day MA'))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df.MA20, line=dict(color='green', width=1), name='20-Day MA'))
    fig.add_trace(go.Scatter(x=tracer_df.index, y=tracer_df['Close'], mode='markers',marker=dict(size=12), name='Event Occurence', hovertext=tracer_df['Tracers']))

    # fig.update_layout(
    #         plot_bgcolor=colors['background'],
    #         paper_bgcolor=colors['background'],
    #         font_color=colors['text'])

    fig.update_layout(title="Visualization of "+display_name+" stock price based on events", height=550, width=1760)
    fig.update_yaxes(title=company+" Price $", secondary_y=False, showgrid=False)

    fig.update_layout(xaxis_rangeslider_visible=False)

    return fig



if st.button('Plot'):
    comp = company_map[company_name]
    print(comp)
    chart = generate_chart(comp, start_date, end_date, company_name)
    st.plotly_chart(chart)

