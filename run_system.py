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
