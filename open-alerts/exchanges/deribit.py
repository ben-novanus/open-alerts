from exchanges.exchange import Exchange
import asyncio
import websockets
import json
import time
import logging
from random import randrange


class Deribit(Exchange):
    def __init__(self, client_id, client_secret, test=False):
        self.logger = logging.getLogger('main')
        self.client_id = client_id
        self.client_secret = client_secret
        self.test = test

        if self.test:
            self.url = "test.deribit.com"
        else:
            self.url = "deribit.com"

    def processAlert(self, alert):
        if not alert.blocks:
            self.logger.warning("No blocks found for Alert. \
Blocks are denoted with a bracketed number i.e. [1]")

        url = "wss://" + self.url + "/ws/api/v2"

        async def call_api():
            async with websockets.connect(url) as websocket:
                # authenticate
                await websocket.send(self.getAuthenticationJson())
                while websocket.open:
                    response = await websocket.recv()
                    j = json.loads(response)
                    if j.get("error"):
                        self.logger.error("Unable to authenticate", j)
                        return

                    # get the ticker
                    await websocket.send(self.getTickerJson(alert.instrument))
                    response = await websocket.recv()
                    j = json.loads(response)
                    ticker = j.get("result")

                    # look up the tick size based on instrument
                    await websocket.send(self.getInstrumentsJson(
                        alert.currency))
                    response = await websocket.recv()
                    j = json.loads(response)
                    ticker["tick_size"] = next((item for item in
                                                j.get("result")
                                                if item['instrument_name'] ==
                                                alert.instrument),
                                               None).get("tick_size")

                    # get the account information
                    # await websocket.send(self.getAccountInfoJson(
                    #     alert.currency))
                    # response = await websocket.recv()
                    # j = json.loads(response)
                    # accountInfo = j.get("result")

                    for block in alert.blocks:
                        if block:
                            self.logger.info("Executing Alert Block")
                            if block.wait:
                                time.sleep(int(block.wait))

                            if block.cancel == "ORDER":
                                await self.cancelOrders(websocket,
                                                        alert,
                                                        block)
                            elif block.close == "POSITION":
                                await self.closePosition(websocket,
                                                         ticker,
                                                         alert,
                                                         block)
                            elif block.order:
                                await self.trade(websocket,
                                                 ticker,
                                                 alert,
                                                 block)

                    # close the websocket
                    await websocket.close()

        asyncio.get_event_loop().run_until_complete(call_api())

    def getJsonMessage(self, method, params):
        return json.dumps({
            "jsonrpc": "2.0",
            "id": randrange(0, 8001, 2),
            "method": method,
            "params": params
        })

    def getAuthenticationJson(self):
        params = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        return self.getJsonMessage("public/auth", params)

    def getAccountInfoJson(self, currency):
        params = {
            "currency": currency,
            "extended": True
        }
        return self.getJsonMessage("private/get_account_summary", params)

    def getTickerJson(self, instrument):
        params = {
            "instrument_name": instrument
        }
        return self.getJsonMessage("public/ticker", params)

    def getInstrumentsJson(self, currency):
        params = {
            "currency": currency,
            "kind": "future",
            "expired": False
        }
        return self.getJsonMessage("public/get_instruments", params)

    def getOpenOrdersJson(self, instrument):
        params = {
            "instrument_name": instrument
        }
        return self.getJsonMessage("private/get_open_orders_by_instrument",
                                   params)

    def getCancelJson(self, order_id):
        params = {
            "order_id": order_id
        }
        return self.getJsonMessage("private/cancel", params)

    def getPositionJson(self, instrument):
        params = {
            "instrument_name": instrument
        }
        return self.getJsonMessage("private/get_position", params)

    def getClosePositionJson(self, ticker, block, position):
        if not position:
            return

        if position.get("size") and \
            ((self.isBid(block.side) and position.get("size") > 0) or
             (self.isAsk(block.side) and position.get("size") < 0) or
                (not block.side and abs(position.get("size")) > 0)):

            method = "private/sell" if position.get("direction") == \
                "buy" else "private/buy"
            params = {
                "instrument_name": position.get("instrument_name"),
                "amount": abs(self.toPrecise(self.changeQuantity(
                    position.get("size"), block.quantity), 0))
            }

            if block.order == "MARKET":
                params["type"] = "market"

            elif block.order == "LIMIT":
                params["type"] = "limit"
                params["price"] = self.toPrecise(
                    self.changePrice(position.get("average_price"),
                                     block.limit_price),
                    ticker.get("tick_size"))
                params["reduce_only"] = True

                if block.post_only == "TRUE":
                    params["post_only"] = True

            elif block.order == "STOP_MARKET":
                params["type"] = "stop_market"
                params["stop_price"] = self.toPrecise(
                    self.changePrice(position.get("average_price"),
                                     block.stop_price),
                    ticker.get("tick_size"))

                if block.trigger == "LAST" or not block.trigger:
                    params["trigger"] = "last_price"
                elif block.trigger == "INDEX":
                    params["trigger"] = "index_price"
                elif block.trigger == "MARK":
                    params["trigger"] = "mark_price"

            elif block.order == "STOP_LIMIT":
                params["type"] = "stop_limit"
                params["price"] = self.toPrecise(
                    self.changePrice(position.get("average_price"),
                                     block.limit_price),
                    ticker.get("tick_size"))
                params["stop_price"] = self.toPrecise(
                    self.changePrice(position.get("average_price"),
                                     block.stop_price),
                    ticker.get("tick_size"))

                if block.post_only == "TRUE":
                    params["post_only"] = True

                if block.trigger == "LAST" or not block.trigger:
                    params["trigger"] = "last_price"
                elif block.trigger == "INDEX":
                    params["trigger"] = "index_price"
                elif block.trigger == "MARK":
                    params["trigger"] = "mark_price"

            elif block.order == "TAKE_PROFIT_MARKET":
                self.logger.warning("'take_profit_market' is not \
a valid order type for Deribit, use a limit order instead for taking profit")
                return

            elif block.order == "TAKE_PROFIT_LIMIT":
                self.logger.warning("'take_profit_limit' is not \
a valid order type for Deribit, use a limit order instead for taking profit")
                return

            return self.getJsonMessage(method, params)

    def getTradeJson(self, ticker, alert, block):
        method = "private/buy" if self.isBid(block.side) else "private/sell"
        params = {
            "instrument_name": alert.instrument,
            "amount": self.toPrecise(block.quantity, 0)
        }

        if block.order == "MARKET":
            params["type"] = "market"

        elif block.order == "LIMIT":
            params["type"] = "limit"
            first = ticker.get("best_bid_price") if self.isBid(
                block.side) else ticker.get("best_ask_price")
            params["price"] = self.toPrecise(
                self.changePrice(first, block.limit_price),
                ticker.get("tick_size"))

            if block.post_only == "TRUE":
                params["post_only"] = True

            if block.reduce_only == "TRUE":
                params["reduce_only"] = True

        elif block.order == "STOP_MARKET":
            params["type"] = "stop_market"
            first = ticker.get("best_bid_price") if self.isAsk(
                block.side) else ticker.get("best_ask_price")
            params["stop_price"] = self.toPrecise(
                self.changePrice(first, block.stop_price),
                ticker.get("tick_size"))

            if block.trigger == "LAST" or not block.trigger:
                params["trigger"] = "last_price"
            elif block.trigger == "INDEX":
                params["trigger"] = "index_price"
            elif block.trigger == "MARK":
                params["trigger"] = "mark_price"

        elif block.order == "STOP_LIMIT":
            params["type"] = "stop_limit"
            first = ticker.get("best_bid_price") if self.isBid(
                block.side) else ticker.get("best_ask_price")
            params["price"] = self.toPrecise(
                self.changePrice(first, block.limit_price),
                ticker.get("tick_size"))
            params["stop_price"] = self.toPrecise(
                self.changePrice(first, block.stop_price),
                ticker.get("tick_size"))

            if block.post_only == "TRUE":
                params["post_only"] = True

            if block.trigger == "LAST" or not block.trigger:
                params["trigger"] = "last_price"
            elif block.trigger == "INDEX":
                params["trigger"] = "index_price"
            elif block.trigger == "MARK":
                params["trigger"] = "mark_price"

        elif block.order == "TRAILING_STOP":
            self.logger.warning("'trailing_stop' is not \
a valid order type for Deribit")
            return

        elif block.order == "TAKE_PROFIT_MARKET":
            self.logger.warning("'take_profit_market' is not \
a valid order type for Deribit, use a limit order instead for taking profit")
            return

        elif block.order == "TAKE_PROFIT_LIMIT":
            self.logger.warning("'take_profit_limit' is not \
a valid order type for Deribit, use a limit order instead for taking profit")
            return

        return self.getJsonMessage(method, params)

    async def cancelOrders(self, websocket, alert, block):
        await websocket.send(self.getOpenOrdersJson(alert.instrument))
        response = await websocket.recv()
        j = json.loads(response)
        orders = j.get("result")

        for order in orders:
            if not block.side or \
                (self.isBid(block.side) and
                 order.get("direction") == "buy") or \
                    (self.isAsk(block.side) and
                     order.get("direction") == "sell"):
                await websocket.send(
                    self.getCancelJson(order.get("order_id")))
                response = await websocket.recv()
                j = json.loads(response)
                if j.get("error"):
                    self.logger.error("Error canceling order with id: " +
                                      order.get("order_id"), j)

    async def closePosition(self, websocket, ticker, alert, block):
        # make sure previous trade completed. retry 5 times and then cancel
        for i in range(5):
            await websocket.send(self.getPositionJson(alert.instrument))
            response = await websocket.recv()
            j = json.loads(response)
            position = j.get("result")

            if position.get("trades") or position.get("order"):
                self.logger.warn("Previous trade/order not completed, \
waiting 1 second and trying again. Attempt " + str(i + 1) + " of 5")
                if i == 4:
                    self.logger.error("Unable to close position, \
previous trade/order could not completed, 5 attempts were made")
                else:
                    time.sleep(1)
            else:
                break

        closeJson = self.getClosePositionJson(ticker, block, position)
        if closeJson:
            await websocket.send(closeJson)
            response = await websocket.recv()
            j = json.loads(response)
            if j.get("error"):
                self.logger.error("Error sending close position", j)

    async def trade(self, websocket, ticker, alert, block):
        tradeJson = self.getTradeJson(ticker, alert, block)
        if tradeJson:
            await websocket.send(tradeJson)
            response = await websocket.recv()
            j = json.loads(response)
            if j.get("error"):
                self.logger.error("Error sending trade", j)
