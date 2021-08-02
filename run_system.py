import operator
import pathlib  # resolve file path issue in different OS
import pprint
import time as true_time
from configparser import ConfigParser
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from py_tradesys.indicators import Indicators
from py_tradesys.tradecenter import Tradecenter

# grab the config file value
config = ConfigParser()
config.read("configs/configs.ini")

CLIENT_ID = config.get("main", "CLIENT_ID")
REDIRECT_URL = config.get("main", "REDIRECT_URL")
CREDENTIAL_PATH = config.get("main", "JSON_PATH")
ACCOUNT_NUMBER = config.get("main", "ACCOUNT_NUMBER")

# initialize trade system

trade_system = Tradecenter(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URL,
    credentials_path=CREDENTIAL_PATH,
    trading_account=ACCOUNT_NUMBER,
    paper_trading=True,
)

# create a new portfolio

trading_sys_portfolio = trade_system.create_portfolio()

# add multiple positions to our portfolio

multi_position = [
    {
        "asset_type": "equity",
        "quantuty": 2,
        "purchase_price": 4.00,
        "symbol": "TSLA",
        "purchase_date": "2021-01-01",
    },
    {
        "asset_type": "equity",
        "quantuty": 2,
        "purchase_price": 4.00,
        "symbol": "AAPL",
        "purchase_date": "2021-01-01",
    },
]

# add those positions to the Portfolio

new_positions = trade_system.portfolio.add_positions(positions=multi_position)

pprint.pprint(new_positions)

print(new_positions)

# add a single positions to the portfolio

trade_system.portfolio.add_position(
    symbol="MSFT", quantity="10", asset_type="equity", purchase_date="2021-07-29"
)
pprint.pprint(trade_system.portfolio.positions)

# check to see if the pre market is open

if trade_system.regular_market_open:
    print("Pre Market Open")
else:
    print("Pre Market is not Open")

# check to see if the post market is open

if trade_system.post_market_open:
    print("Post Market Open")
else:
    print("Post Market is not Open")

# grab the current quote in our portfolio

current_quote = trade_system.grab_current_quotes()
# pprint.pprint(current_quote)

# define the date range

end_data = datetime.today()
start_date = end_data - timedelta(days=30)

# grab the historical price

historical_prices = trade_system.grab_historical_prices(
    start=start_date, end=end_data, bar_size=1, bar_type="minute"
)

# convert the data into a stockfrome

stock_frame = trade_system.create_stock_frame(data=historical_prices["aggregated"])

# print the head

pprint.pprint(stock_frame.frame.head(n=20))

# create a new trade object

new_trade = trade_system.create_trade(
    trade_id="long_msft",
    enter_or_exit="enter",
    long_or_short="long",
    order_type="lmt",
    price=150.00,
)

# cancel the order during certain period

new_trade.good_till_cancel(
    cancel_time=datetime.now() + timedelta(minutes=90)
)  # cancel the order 90 min from now

# change the session

new_trade.modify_session(session="am")

# add order leg

new_trade.instrument(symbol="MSFT", quantity=2, asset_type="EQUITY")


# add a stop loss order with the main order
# 0.1 below the current price and indicate is NOT percentage

new_trade.add_stop_loss(stop_size=0.10, percentage=False)

pprint.pprint(new_trade.order)

# create a new indicator client

indicator_client = Indicators(price_data_frame=stock_frame)

# add the RSI
indicator_client.rsi(period=14)

indicator_client.sma(period=200)

indicator_client.ema(period=50)

# add the signal to check for it

indicator_client.set_indicator_signals(
    indicator="rsi", buy=40.0, sell=20.0, condition_buy=operator.ge, condition_sell=operator.le
)

# define a trade dict

trade_dict = {
    "MSFT": {
        "trade_func": trade_system.trades["long_msft"],
        "trade_id": trade_system.trades["long_msft"].trade_id,
    }
}

while True:

    # grab the latest bar
    latest_bars = trade_system.get_latest_bar()

    # add those bar to the stockframe
    stock_frame.add_rows(data=latest_bars)

    # refresh indicator
    indicator_client.refresh()
