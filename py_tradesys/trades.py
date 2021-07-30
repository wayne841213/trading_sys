from datetime import datetime, time, timezone
from typing import Dict, List, Optional, Union

import pandas as pd


class Trades:
    def __init__(self):

        self.order = {}
        self.trade_id = ""

        self.side = ""
        self.side_oppsite = ""
        self.enter_or_exit = ""
        self.enter_or_exit_opposite = ""

        self._order_response = {}
        self._triggered_added = False
        self._multi_leg = False

    def new_trade(
        self,
        trade_id: str,
        order_type: str,
        side: str,
        enter_or_exit: str,
        price: float = 0.00,
        stop_limit_price: float = 0.00,
    ):

        self.trade_id = trade_id

        self.order_type = {
            "mkt": "MARKET",  # cap because TD Api request
            "lmt": "LIMIT",
            "stop": "STOP",
            "stop_lmt": "STOP_LIMIT",
            "trailing_stop": "TRAILING_STOP",
        }

        self.order_instructions = {
            "enter": {"long": "Buy", "short": "SELL_SHORT"},
            "exit": {"long": "SELL", "short": "BUY_TO_COVER"},
        }

        self.order = {
            "orderStrategyType": "SINGLE",
            "orderType": self.order_type[order_type],
            "session": "NORMAL",
            "duration": "DAY",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[enter_or_exit][side],
                    "quantity": 0,
                    "instrument": {"symbol": None, "assetType": None},
                }
            ],
        }

        if self.order["orderType"] == "STOP":
            self.order["stopPrice"] = price

        elif self.order["orderType"] == "LIMIT":
            self.order["price"] = price

        elif self.order["orderType"] == "STOP_LIMIT":
            self.order["stopPrice"] = price
            self.order["price"] = stop_limit_price

        elif self.order["orderType"] == "TRAILING_STOP":
            self.order["stopPriceLinkBasis"] = ""
            self.order["stopPriceLinkType"] = ""
            self.order["stopPriceOffset"] = 0.0
            self.order["stopType"] = "STANDARD"

        self.enter_or_exit = enter_or_exit
        self.side = side
        self.order_types = order_type
        self.price = price

        # store import info for later use
        if order_type == "stop":
            self.stop_price = price
        elif order_type == "stop_lmt":
            self.stop_price = price
            self.stop_limit_price = stop_limit_price
        else:
            self.stop_price = 0.0

        # store important side info
        if self.enter_or_exit == "enter":
            self.enter_or_exit_opposite == "exit"
        elif self.enter_or_exit == "exit":
            self.enter_or_exit_opposite == "enter"

        if self.side == "long":
            self.side_oppsite == "short"
        elif self.side == "short":
            self.side_oppsite == "long"

    def instrument(
        self,
        symbol: str,
        quantity: int,
        asset_type: str,
        sub_asset_type: str = None,
        order_leg_id: int = 0,
    ):

        leg = self.order["orderLegCollection"][order_leg_id]

        leg["instrument"]["symbol"] = symbol
        leg["instrumnent"]["asset_type"] = asset_type
        leg["quantity"] = quantity

        self.order_size = quantity
        self.symbol = symbol
        self.asset_type = asset_type

        return leg

    def good_till_cancel(self, cancel_time: datetime):

        self.order["duration"] = "GOOD_TILL_CANCEL"
        self.order["cancelTime"] = cancel_time.isoformat()

    def modify_side(self, side: Optional[str], order_leg_id: int = 0):

        if side and side not in ["buy", "sell", "sell_short", "buy_to_cover"]:
            raise ValueError("You need a valid side!")

        if side:
            self.side["orderLegCollection"][order_leg_id]["instructions"] = side.upper
        # assume you don't pass anything that you want the opposite side
        else:
            self.side["orderLegCollection"][order_leg_id]["instructions"] = self.order_instructions[
                self.enter_or_exit
            ][self.side_oppsite]

    def add_box_range(  # maybe rename
        self, profit_size: float = 0.00, percentage: bool = False, stop_limit: bool = False
    ):

        if not self._triggered_added:
            self._convert_to_trigger()

        self.add_take_profit(profit_size=profit_size, percentage=percentage)

        if not stop_limit:
            self.add_stop_loss(stop_size=profit_size, percentage=percentage)

    def add_stop_loss(self, stop_size: float, percentage: bool = False) -> bool:

        if not self._triggered_added:
            self._convert_to_trigger()

        if self.order_type == "mkt":
            pass
            # get quote

        if self.order_types == "lmt":
            price = self.price

        if percentage:
            adjustment = 1.0 - stop_size
            new_price = self._calculate_new_price(
                price=price, adjustment=adjustment, percentage=True
            )
        else:
            adjustment = -stop_size
            new_price = self._calculate_new_price(
                price=price, adjustment=adjustment, percentage=False
            )

        stop_loss_order = {
            "orderType": "STOP",
            "session": "NORMAL",
            "duration": "DAY",
            "stopPrice": new_price,
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {"symbol": self.symbol, "assetType": self.asset_type},
                }
            ],
        }

        self.stop_loss_order = stop_loss_order
        self.order["childOrderStrategies"].append(self.stop_loss_order)

        return True

    def add_stop_limit(
        self,
        stop_size: float,
        limit_size: float,
        stop_percentage: bool = False,
        limit_percentage: bool = False,
    ):

        if not self._triggered_added:
            self._convert_to_trigger()

        if self.order_type == "mkt":
            pass
            # get quote

        if self.order_types == "lmt":
            price = self.price

        if stop_percentage:
            adjustment = 1.0 - stop_size
            stop_price = self._calculate_new_price(
                price=price, adjustment=adjustment, percentage=True
            )
        else:
            adjustment = -stop_size
            stop_price = self._calculate_new_price(
                price=price, adjustment=adjustment, percentage=False
            )

        if limit_percentage:
            adjustment = 1.0 - limit_size
            limit_price = self._calculate_new_price(
                price=price, adjustment=adjustment, percentage=True
            )
        else:
            adjustment = -limit_size
            limit_price = self._calculate_new_price(
                price=price, adjustment=adjustment, percentage=False
            )

        stop_limit_order = {
            "orderType": "STOP_LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "price": limit_price,
            "stopPrice": stop_price,
            "orderStrategyType": "SINGLE",
            "orderlegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {"symbol": self.symbol, "assetType": self.asset_type},
                }
            ],
        }

        self.stop_limit_order = stop_limit_order
        self.order["childOrderStrategies"].append(self.stop_limit_order)

        return True

    def _calculate_new_price(self, price: float, adjustment: float, percentage: bool):

        if percentage:
            new_price = price * adjustment
        else:
            new_price = price + adjustment

        # especially for TD API
        if new_price < 1:
            new_price = round(new_price, 4)

        else:
            new_price = round(new_price, 2)

        return new_price

    def add_take_profit(self, profit_size: float, percentage: bool = False):

        if not self._triggered_added:
            self._convert_to_trigger()

        if self.order_type == "mkt":
            pass
            # get quote

        if self.order_types == "lmt":
            price = self.price

        if percentage:
            adjustment = 1.0 - profit_size
            profit_price = self._calculate_new_price(
                price=price, adjustment=adjustment, percentage=True
            )
        else:
            adjustment = -profit_size
            profit_price = self._calculate_new_price(
                price=price, adjustment=adjustment, percentage=False
            )

        # build the order
        take_profit_order = {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "price": profit_price,
            "orderStrategyType": "SINGLE",
            "orderlegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {"symbol": self.symbol, "assetType": self.asset_type},
                }
            ],
        }

        self.take_profit_order = take_profit_order
        self.order["childOrderStrategies"].append(self.take_profit_order)

        return True

    def _convert_to_trigger(self):

        if self.order and self._triggered_added == False:
            self.order["orderStrategyType"] = "TRIGGER"
            self.order["childOrderStrategies"] = []
            self._triggered_added = True

    def modify_session(self, session: str):

        if session in ["am", "pm", "normal", "seamless"]:
            self.order["session"] = session.upper()
        else:
            raise ValueError("Invalid Session!")

    # get the value
    @property
    def order_response(self):
        # saving the order the data -> the actual order you send to TD

        return self._order_response

    # set the value
    @order_response.setter
    def order_response(self, order_response_dict: dict):

        self._order_response = order_response_dict

    def _generate_order_id(self):

        if self.order:

            order_id = "{symbol}_{side}_{enter_or_exit}_{timestamp}"

            order_id = order_id.format(
                symbol=self.symbol,
                side=self.side,
                enter_or_exit=self.enter_or_exit,
                timestamp=datetime.now().timestamp(),
            )
            return order_id
        else:

            return ""

    def add_leg(
        self,
        order_leg_id: int,
        symbol: str,
        quantity: int,
        asset_type: str,
        sub_asset_type: str = None,
    ):

        # define the leg
        leg = {}
        leg["instrument"]["symbol"] = symbol
        leg["instrument"]["quantity"] = quantity
        leg["instrument"]["asset_type"] = asset_type

        # deal with the sub asset type

        if sub_asset_type:
            leg["instrument"]["sub_asset_type"] = sub_asset_type

        if order_leg_id == 0:
            self.instrument(
                symbol=symbol,
                asset_type=asset_type,
                quantity=quantity,
                sub_asset_type=sub_asset_type,
                order_leg_id=0,
            )
        else:
            order_leg_id: list = self.order["orderLegCollection"]
            order_leg_id.insert(order_leg_id, leg)

        return self.order["orderLegCollection"]

    @property
    def number_of_legs(self):

        return len(self.order["oderLegCollection"])

