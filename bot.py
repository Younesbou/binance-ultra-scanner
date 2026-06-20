import ccxt
import pandas as pd
import numpy as np
import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": msg})

exchange = ccxt.binance()
markets = exchange.load_markets()
symbols = [s for s in markets if s.endswith("/USDT")]

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def vwap(df):
    return (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

def check(symbol):
    try:
        df = exchange.fetch_ohlcv(symbol, "15m", limit=100)
        df = pd.DataFrame(df, columns=['t','o','h','l','c','v'])

        df['rsi'] = rsi(df['c'])

        mab = df['rsi'].rolling(2).mean()
        mbb = df['rsi'].rolling(7).mean()

        vpoc = vwap(df)
        price = df['c'].iloc[-1]

        condition = (
            abs(mab.iloc[-1] - mbb.iloc[-1]) < 6 and
            abs(price - vpoc.iloc[-1]) / price < 0.005 and
            df['rsi'].rolling(34).std().iloc[-1] < 7
        )

        if condition:
            send(f"🚨 SIGNAL\n\n{symbol}\nPrice: {price}")

    except:
        pass

while True:
    for s in symbols:
        check(s)

    time.sleep(900)
