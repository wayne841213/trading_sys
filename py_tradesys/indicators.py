import operator
from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from py_tradesys.asset import StockFrame


class Indicators:
    def __init__(self, price_data_frame: StockFrame) -> None:

        self._stock_frame: StockFrame = price_data_frame
        self._price_groups = self._stock_frame.symbol_groups
        self._current_indicators = {}
        self._indicator_signals = {}
        self.__frame = self._stock_frame.frame

        """
        buy and sell threshod for float
        for example
        RSI > 90.0 then buy, RSI < 10.0 then sell
        """

    def set_indicator_signals(
        self, indicator: str, buy: float, sell: float, condition_buy: Any, condition_sell: Any
    ) -> None:

        # if there is no signal for that indicator set a template
        if indicator not in self._indicator_signals:
            self._indicator_signals[indicator] = {}  # can overwrite it

        # modify the signal
        self._indicator_signals[indicator]["buy"] = buy
        self._indicator_signals[indicator]["sell"] = sell
        self._indicator_signals[indicator]["buy_operator"] = condition_buy
        self._indicator_signals[indicator]["sell_operator"] = condition_sell

    def get_indicator_signals(self, indicator: Optional[str]) -> Dict:

        if indicator and indicator in self._indicator_signals:
            return self._indicator_signals[indicator]

        # if you don't give me indicator, just give you everthing
        else:
            return self._indicator_signals

    @property
    def price_data_frame(self) -> pd.DataFrame:
        return self._frame

    @price_data_frame.setter
    def price_data_frame(self, price_data_frame: pd.DataFrame) -> None:

        self._frame = price_data_frame

    # calculate the indicator

    # ROC indicator

    def change_in_price(self) -> pd.DataFrame:

        locals_data = locals()
        del locals_data["self"]
        # show every argument pass through this function, and the location is critical

        column_name = "change_in_price"
        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]["args"] = locals_data
        self._current_indicators[column_name]["func"] = self.change_in_price

        # calculate the indicator itself

        self._frame[column_name] = self._price_groups["close"].transform(lambda x: x.diff())

    # RSI
    def rsi(self, period: int, method: str = "wilders") -> pd.DataFrame:

        locals_data = locals()
        del locals_data["self"]

        column_name = "rsi"
        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]["args"] = locals_data
        self._current_indicators[column_name]["func"] = self.rsi

        if "change_in_price" not in self._frame.columns:
            # to see whether the ROC is in the column, if not then calculate for them
            self.change_in_price()

        # Define the up day

        self._frame["up_day"] = self._price_groups["change_in_price"].transform(
            lambda x: np.where(x >= 0, x, 0)
        )

        self._frame["down_day"] = self._price_groups["change_in_price"].transform(
            lambda x: np.where(x < 0, x.abs(), 0)
        )

        self._frame["ewma_up"] = self._price_groups["up_day"].transform(
            lambda x: x.ewm(span=period).mean()
        )

        self._frame["ewma_down"] = self._price_groups["down_day"].transform(
            lambda x: x.ewm(span=period).mean()
        )

        relative_strength = self._frame["ewma_up"] / self._frame["ewma_down"]

        relative_strength_index = 100.0 - (100.0 / (1.0 + relative_strength))

        # add RSI indicator to the data
        self._frame["rsi"] = np.where(relative_strength_index == 0, 100, relative_strength_index)

        # clean up before sending back
        self._frame.drop(
            labels=["ewma_up", "ewma_down", "up_day", "down_day", "change_in_price"],
            axis=1,
            inplace=True,
        )

        return self._frame

    # SMA

    def sma(self, period: int) -> pd.DataFrame:

        locals_data = locals()
        del locals_data["self"]

        column_name = "sma"
        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]["args"] = locals_data
        self._current_indicators[column_name]["func"] = self.sma

        # add the sma
        self._frame[column_name] = self._price_groups["close"].transform(
            lambda x: x.rolling(period).mean()
        )

        return self._frame

    # EMA

    def ema(self, period: int, alpha: float = 0.0) -> pd.DataFrame:

        locals_data = locals()
        del locals_data["self"]

        column_name = "ema"
        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]["args"] = locals_data
        self._current_indicators[column_name]["func"] = self.ema

        # add ema

        self._frame[column_name] = self._price_groups["close"].transform(
            lambda x: x.ewm(span=period).mean()
        )

        return self._frame
        """
        add more indicator
        """

    def refresh(self):

        # update the group first
        self._price_groups = self._stock_frame.symbol_groups
        # loop through all the indicator

        for indicator in self._current_indicators:

            indicator_argument = self._current_indicators[indicator]["args"]
            indicator_function = self._current_indicators[indicator]["func"]

            # update the columns

            indicator_function(**indicator_argument)
        """
        unpacked dictionary
        example 
        def add(a=0, b=0):
        return a + b
        d = {'a': 2, 'b': 3}

        add(**d)
        the result will generate 2+3(add function) = 5
        """

    def check_signal(self) -> Union[pd.DataFrame, None]:

        signal_df = self._stock_frame._chech_signal(indicators=self._indicator_signals)

        return signal_df

