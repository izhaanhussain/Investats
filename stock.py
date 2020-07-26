import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import time

api_key = 'demo'

ts = TimeSeries(key=api_key, output_format='pandas')

def getCurrentPrice(ticker):
    data, meta_data = ts.get_intraday(symbol=ticker, interval = '60min', outputsize = 'compact')
    s = data['1. open']
    dataNeeded = str(s[1])
    return dataNeeded