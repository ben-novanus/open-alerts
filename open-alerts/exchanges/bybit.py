from exchanges.exchange import Exchange
import asyncio
import websockets
import json
import time
from datetime import datetime
import hmac
import requests
import collections
from random import randrange
from models.block import Type as BlockType
from models.block import OrderType
from models.block import Direction
from models.block import Trigger
from plugins.plugin_loader import PluginLoader


class ByBit(Exchange):
    def __init__(self, api_key, api_secret, test=False):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.test = test
        self.time_padding = 0

        if self.test:
            self.url = "api-testnet.bybit.com"
        else:
            self.url = "api.bybit.com"

    def processAlert(self, alert):
        if not alert.blocks:
            self.logger.error("No blocks found for alert")
        else:
            self.logger.info("Processing alert for account: %s", alert.account)

            for block in alert.blocks:
                if block and block.type:
                    if block.wait:
                        self.logger.info("Waiting %s seconds", block.wait)
                        time.sleep(int(block.wait))

                    self.logger.info("Executing Block: %s",
                                     block.type.value)

                    if block.type == BlockType.CANCEL_ORDER:
                        self.cancelOrders(alert,
                                          block)
                    elif block.type == BlockType.CLOSE_POSITION:
                        self.closePosition(alert,
                                           block)
                    elif block.type == BlockType.STANDARD_ORDER:
                        self.trade(alert,
                                   block)
                    elif block.type == BlockType.ADJUST_POSITION:
                        self.adjustPosition(alert,
                                            block)
                    elif block.type == BlockType.PLUGIN:
                        continueProcessingBlocks = PluginLoader.processPluginBlock(alert,
                                                                      block)
                        if not continueProcessingBlocks:
                            self.logger.warning(
                                "Plugin %s returned False, skipping remaining blocks for alert", block.plugin)
                            return

    def getRequestResponse(self, method, resource, params):
        try:
            if method == "POST":
                r = requests.post("https://" + self.url +
                                  resource, data=self.getSignedParams(params))
            elif method == "GET":
                r = requests.get("https://" + self.url + resource,
                                 params=self.getSignedParams(params))
            else:
                self.logger.error(
                    "Unknown method when attempting to do request: %s", method)
                return
        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            self.logger.error("Timeout encountered, exiting")
            return
        except requests.exceptions.TooManyRedirects:
            self.logger.error(
                "Too many redirects encountered when doing request, possible bad url")
            return
        except requests.exceptions.RequestException as e:
            self.logger.error("Unable to complete request: %s", e)
            return

        if r.status_code == 200:
            return r
        else:
            self.logger.error(
                "Error from ByBit response, code: %s", r.status_code)
            return

    def getSignedParams(self, params):
        params["api_key"] = self.api_key
        params["timestamp"] = int(
            datetime.now().timestamp() * 1000) - 1000 - self.time_padding
        params["recv_window"] = 20000

        ordered_params = collections.OrderedDict(sorted(params.items()))
        ordered_params["sign"] = self.getSignature(ordered_params)

        return ordered_params

    def getSignature(self, ordered_params):
        _val = '&'.join([str(k) + "=" + str(v)
                         for k, v in ordered_params.items() if (k != 'sign') and (v is not None)])

        return str(hmac.new(bytes(self.api_secret, "utf-8"), bytes(_val, "utf-8"), digestmod="sha256").hexdigest())

    def getTicker(self, symbol):
        resource = "/v2/public/tickers"
        params = {"symbol": symbol}
        self.logger.debug(
            "Get Ticker, Resource: %s, Params: %s", resource, params)
        response = self.getRequestResponse("GET", resource, params)
        if response:
            return response.json()
        else:
            return

    def getActiveOrders(self, params, filter):
        return self.getOrders(params, filter, "/open-api/order/list")

    def getConditionalOrders(self, params, filter):
        return self.getOrders(params, filter, "/open-api/stop-order/list")

    def getOrders(self, params, filter, resource):
        self.logger.debug(
            "Get Orders, Resource: %s, Params: %s, Filter: %s", resource, params, filter)
        response = self.getRequestResponse("GET", resource, params)
        if response:
            j = response.json()
            if self.isErrorResponse("get orders", j):
                return []
            orders = j.get("result").get("data")
            if filter:
                ret = []
                for filterKey, filterVal in filter.items():
                    for order in orders:
                        if order.get(filterKey) == filterVal:
                            ret.append(order)
                return ret
            else:
                return orders
        else:
            return

    def getPosition(self, symbol):
        resource = "/v2/private/position/list"
        params = {"symbol": symbol}
        self.logger.debug(
            "Get Position, Resource: %s, Params: %s", resource, params)
        response = self.getRequestResponse("GET", resource, params)
        if response:
            j = response.json()
            if self.isErrorResponse("get position", j):
                return

            position = j.get("result")
            if float(position.get("position_value")) > 0:
                return position
            else:
                return
        else:
            return

    def getBalance(self, symbol):
        position = self.getPosition(symbol)
        if position:
            return position.get("wallet_balance")
        return

    def hasPosition(self, symbol, direction):
        position = self.getPosition(symbol)
        if position:
            if direction == Direction.BUY and position.get("side") == "Buy":
                return True
            elif direction == Direction.SELL and position.get("side") == "Sell":
                return True
        return False

    def cancelOrders(self, alert, block):
        filter = {}
        if block.direction == Direction.BUY:
            filter["side"] = "Buy"
        elif block.direction == Direction.SELL:
            filter["side"] = "Sell"

        params = {
            "symbol": alert.symbol,
            "order_status": "Created,New,PartiallyFilled"
        }
        orders = self.getActiveOrders(params, filter)

        filter["stop_order_status"] = "Untriggered"
        params = {"symbol": alert.symbol}
        orders += self.getConditionalOrders(params, filter)

        for order in orders:
            params = {"symbol": alert.symbol}
            if order.get("order_id"):
                resource = "/v2/private/order/cancel"
                params["order_id"] = order.get("order_id")
            else:
                resource = "/open-api/stop-order/cancel"
                params["stop_order_id"] = order.get("stop_order_id")

            self.logger.debug(
                "Cancel Orders, Resource: %s, Params: %s", resource, params)
            response = self.getRequestResponse("POST", resource, params)
            if response:
                self.logResponse("cancel orders", response.json())

    def closePosition(self, alert, block):
        position = self.getPosition(alert.symbol)
        if not position:
            self.logger.info("No open positions found for params")
            return

        if ((block.direction == Direction.BUY and position.get("side") != "Buy") or
                (block.direction == Direction.SELL and position.get("side") != "Sell")):
            self.logger.info(("Ignoring close position because the currently open "
                              "position direction: %s does not match block direction: %s"),
                             position.get("side"), block.direction.value)
            return

        j = self.getTicker(alert.symbol)
        if self.isErrorResponse("ticker request", j):
            return
        ticker = j.get("result")[0]

        params = {
            "symbol": alert.symbol,
            "time_in_force": "GoodTillCancel",
            "qty": round(float(self.changeQuantity(position.get("size"), block.quantity)))
        }
        if position.get("side") == "Buy":
            params["side"] = "Sell"
        else:
            params["side"] = "Buy"

        if block.orderType == OrderType.MARKET or not block.orderType:
            params["order_type"] = "Market"
            params["price"] = ticker.get("last_price")
        elif block.orderType == OrderType.LIMIT:
            params["order_type"] = "Limit"
            if block.limit_price_m:
                params["price"] = self.toPrecise(
                    self.changePrice(ticker.get("last_price"),
                                     block.limit_price_m),
                    alert.symbol,
                    False
                )
            else:
                params["price"] = self.toPrecise(
                    self.changePrice(position.get(
                        "entry_price"), block.limit_price),
                    alert.symbol,
                    False
                )
            if block.post_only == "TRUE":
                params["time_in_force"] = "PostOnly"
            params["reduce_only"] = True
        elif block.orderType == OrderType.STOP_MARKET:
            params["order_type"] = "Market"
            if block.direction == Direction.BUY:
                first = ticker.get("bid_price")
            else:
                first = ticker.get("ask_price")
            params["base_price"] = self.toPrecise(
                position.get("entry_price"), alert.symbol, False)
            params["price"] = self.toPrecise(
                position.get("entry_price"), alert.symbol, False)
            if block.stop_price_m:
                params["stop_px"] = self.toPrecise(
                    self.changePrice(ticker.get("last_price"),
                                     block.stop_price_m),
                    alert.symbol,
                    False
                )
            else:
                params["stop_px"] = self.toPrecise(
                    self.changePrice(position.get(
                        "entry_price"), block.stop_price),
                    alert.symbol,
                    False
                )
            params["close_on_trigger"] = True
        elif block.orderType == OrderType.STOP_LIMIT:
            params["order_type"] = "Limit"
            if block.direction == Direction.BUY:
                first = ticker.get("bid_price")
            else:
                first = ticker.get("ask_price")
            params["base_price"] = self.toPrecise(
                position.get("entry_price"), alert.symbol, False)
            if block.limit_price_m:
                params["price"] = self.toPrecise(
                    self.changePrice(ticker.get("last_price"),
                                     block.limit_price_m),
                    alert.symbol,
                    False
                )
            else:
                params["price"] = self.toPrecise(
                    self.changePrice(position.get(
                        "entry_price"), block.limit_price),
                    alert.symbol,
                    False
                )
            if block.stop_price_m:
                params["stop_px"] = self.toPrecise(
                    self.changePrice(ticker.get("last_price"),
                                     block.stop_price_m),
                    alert.symbol,
                    False
                )
            else:
                params["stop_px"] = self.toPrecise(
                    self.changePrice(position.get(
                        "entry_price"), block.stop_price),
                    alert.symbol,
                    False
                )
            params["close_on_trigger"] = True
            if block.post_only:
                params["time_in_force"] = "PostOnly"

        if block.orderType == OrderType.STOP_MARKET or block.orderType == OrderType.STOP_LIMIT:
            resource = "/open-api/stop-order/create"
        else:
            resource = "/v2/private/order/create"
        self.logger.debug(
            "Close Position, Resource: %s, Params: %s", resource, params)
        response = self.getRequestResponse("POST", resource, params)
        if response:
            self.logResponse("close position", response.json())

    def trade(self, alert, block):
        j = self.getTicker(alert.symbol)
        if self.isErrorResponse("ticker request", j):
            return
        ticker = j.get("result")[0]

        params = {
            "symbol": alert.symbol,
            "time_in_force": "GoodTillCancel",
            "qty": round(float(block.quantity))
        }
        if block.direction == Direction.BUY:
            params["side"] = "Buy"
        else:
            params["side"] = "Sell"

        if block.orderType == OrderType.MARKET:
            params["order_type"] = "Market"

            if block.direction == Direction.BUY:
                params["price"] = ticker.get("bid_price")
            else:
                params["price"] = ticker.get("ask_price")

            if block.take_profit:
                params["take_profit"] = self.toPrecise(
                    self.changePrice(ticker.get("last_price"),
                                     block.take_profit),
                    alert.symbol,
                    False
                )

            if block.stop_loss:
                params["stop_loss"] = self.toPrecise(
                    self.changePrice(ticker.get(
                        "last_price"), block.stop_loss),
                    alert.symbol,
                    False
                )
        elif block.orderType == OrderType.LIMIT:
            params["order_type"] = "Limit"

            if block.direction == Direction.BUY:
                first = ticker.get("bid_price")
            else:
                first = ticker.get("ask_price")

            params["price"] = self.toPrecise(
                self.changePrice(first, block.limit_price),
                alert.symbol,
                False
            )

            if block.take_profit:
                params["take_profit"] = self.toPrecise(
                    self.changePrice(params.price, block.take_profit),
                    alert.symbol,
                    False
                )

            if block.stop_loss:
                params["stop_loss"] = self.toPrecise(
                    self.changePrice(params.price, block.stop_loss),
                    alert.symbol,
                    False
                )

            if block.post_only:
                params["time_in_force"] = "PostOnly"
            if block.reduce_only:
                params["reduce_only"] = True
            elif block.orderType == OrderType.STOP_MARKET:
                params["order_type"] = "Market"

            if block.direction == Direction.BUY:
                first = ticker.get("bid_price")
            else:
                first = ticker.get("ask_price")

            params["base_price"] = first
            params["price"] = first
            params["stop_px"] = self.toPrecise(
                self.changePrice(first, block.stop_price),
                alert.symbol,
                False
            )

            if block.close_on_trigger:
                params["close_on_trigger"] = True
            elif block.orderType == OrderType.STOP_LIMIT:
                params["order_type"] = "Limit"

            if block.direction == Direction.BUY:
                first = ticker.get("bid_price")
            else:
                first = ticker.get("ask_price")

            params["base_price"] = first
            params["price"] = self.toPrecise(
                self.changePrice(first, block.limit_price),
                alert.symbol,
                False
            )
            params["stop_px"] = self.toPrecise(
                self.changePrice(first, block.stop_price),
                alert.symbol,
                False
            )
            if block.close_on_trigger:
                params["close_on_trigger"] = True
            if block.post_only:
                params["time_in_force"] = "PostOnly"

        if self.isPercent(block.quantity):
            balance = self.getBalance(alert.symbol)
            if not balance:
                self.logger.error(
                    "Unable to get balance from current position")
                return
            price = params.price
            qty = price * \
                self.referenceBalance(
                    balance - balance * 0.0015, block.quantity)
            params["qty"] = round(float(qty))
        else:
            params["qty"] = round(float(block.quantity))

        if block.new_position_only:
            if self.hasPosition(alert.symbol, block.direction):
                self.logger.warning(
                    "Block canceled because position in the same direction exists and new_position_only set to true")
                return

        if block.leverage:
            j = self.setLeverage(alert.symbol, block.leverage)

        if block.orderType == OrderType.STOP_MARKET or block.orderType == OrderType.STOP_LIMIT:
            resource = "/open-api/stop-order/create"
        else:
            resource = "/v2/private/order/create"
        self.logger.debug("Trade, Resource: %s, Params: %s", resource, params)
        response = self.getRequestResponse("POST", resource, params)
        if response:
            self.logResponse("trade", response.json())

    def adjustPosition(self, alert, block):
        position = self.getPosition(alert.symbol)
        if not position:
            self.logger.info("No open positions found for params")
            return

        if ((block.direction == Direction.BUY and position.get("side") != "Buy") or
                (block.direction == Direction.SELL and position.get("side") != "Sell")):
            self.logger.info("No open positions found for given direction: %s",
                             block.direction.value)
            return

        j = self.getTicker(alert.symbol)
        if self.isErrorResponse("ticker request", j):
            return
        ticker = j.get("result")[0]

        params = {
            "symbol": alert.symbol
        }
        if block.take_profit:
            params["take_profit"] = self.toPrecise(
                self.changePrice(position.get(
                    "entry_price"), block.take_profit),
                alert.symbol,
                False
            )
        if block.stop_loss:
            params["stop_loss"] = self.toPrecise(
                self.changePrice(position.get(
                    "entry_price"), block.stop_loss),
                alert.symbol,
                False
            )
        if block.trailing_stop:
            params["trailing_stop"] = self.toPrecise(
                self.absolutePercent(
                    ticker.get("last_price"), block.trailing_stop),
                alert.symbol,
                True
            )

        if block.in_profit_only:
            if not self.inProfit(
                float(position.get("entry_price")),
                position.get("side"),
                float(ticker.get("last_price")),
                block.in_profit_only
            ):
                self.logger.warning(
                    "Block cancelled because you're not in profit")
                return

        resource = "/open-api/position/trading-stop"
        self.logger.debug(
            "Adjust Position, Resource: %s, Params: %s", resource, params)
        response = self.getRequestResponse("POST", resource, params)
        if response:
            self.logResponse("adjust position", response.json())

    def setLeverage(self, symbol, leverage):
        self.logger.info("Setting leverage to %s for %s",
                         block.leverage, alert.symbol)

        resource = "/user/leverage/save"
        params = {
            "symbol": symbol,
            "leverage": leverage
        }

        self.logger.debug(
            "Set Leverage, Resource: %s, Params: %s", resource, params)
        response = self.getRequestResponse("POST", resource, params)
        if response:
            self.logResponse("set leverage", response.json())
        else:
            self.logger.error("Unable to get response after setting leverage")

    def toPrecise(self, num, symbol, useMin):
        if symbol == "BTCUSD":
            step = 0.5
        elif symbol == "EOSUSD":
            step = 0.001
        elif symbol == "XRPUSD":
            step = 0.0001
        elif symbol == "ETHUSD":
            step = 0.05
        else:
            step = 1.0

        inv = 1.0 / step
        res = round(float(num) * inv) / inv

        if res == 0 and num > 0:
            if useMin:
                return step
            else:
                return 0
        else:
            return res
