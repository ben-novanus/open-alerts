import logging
import math
from models.block import Direction


class Exchange:
    def __init__(self):
        self.logger = logging.getLogger('main')

    def isPercent(self, num):
        return "%" in num

    def changePrice(self, first, input):
        changeObj = self.isChange(input)
        first = float(first)

        self.logger.debug(
            "Change Price, first: %s, changeObj: %s", first, changeObj)

        if not changeObj:
            return float(input) or first
        else:
            if changeObj.get("percent"):
                if changeObj.get("sign") == "plus":
                    return first * (1 + changeObj.get("num") / 100)
                else:
                    return first * (1 - changeObj.get("num") / 100)
            else:
                if changeObj.get("sign") == "plus":
                    return first + changeObj.get("num")
                else:
                    return first - changeObj.get("num")

    def isChange(self, num):
        num = str(num)
        if not num.startswith("+") and not num.startswith("-"):
            return False
        sign = "plus" if num.startswith("+") else "minus"
        if self.isPercent(num):
            s = slice(1, len(num) - 1)
            return {"num": float(num[s]),
                    "sign": sign,
                    "percent": True}
        else:
            s = slice(1, len(num))
            return {"num": float(num[s]),
                    "sign": sign,
                    "percent": False}

    def changeQuantity(self, position, quantity):
        if not quantity:
            return float(position)

        if quantity.endswith("%"):
            num = quantity.strip("%")
            quantity = position * float(num) / 100

        if abs(position) - float(quantity) > 0:
            return float(quantity)
        else:
            return float(position)

    def inProfit(self, entry, direction, last, profit):
        if profit == "TRUE":
            diff = 0
        elif (self.isPercent(profit)):
            diff = (float(profit) * entry) / 100
        else:
            diff = int(profit)
            if direction == Direction.BUY:
                if diff > 0:
                    return last > entry + diff
                else:
                    return last < entry + diff
            elif direction == Direction.SELL:
                if diff > 0:
                    return last < entry - diff
                else:
                    return last > entry - diff

    def referenceBalance(self, balance, quantity):
        if self.isPercent(quantity):
            diff = float(quantity.strip("%"))
            return balance * (diff / 100)
        else:
            return float(quantity)

    def logResponse(self, requestName, json):
        self.isErrorResponse(requestName, json)

    def isErrorResponse(self, requestName, json):
        if (not json or
            json.get("error") or
                (json.get("ret_code") and json.get("ret_code") != 0)):
            self.logger.error(
                "Error received after sending %s: %s", requestName, json)
            return True
        else:
            self.logger.debug(
                "Response received after sending %s: %s", requestName, json)
            return False

    def absolutePercent(self, first, input):
        if not self.isPercent(input):
            if float(input) == 0:
                res = 0
            else:
                res = input
            return abs(float(res))
        else:
            first = float(first)
            res = float(input.strip("%"))
            return (first * abs(res)) / 100
