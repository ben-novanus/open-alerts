import logging
import math


class Exchange:
    def __init__(self):
        self.logger = logging.getLogger('main')

    def isPercent(self, num):
        return "%" in num

    def toPrecise(self, num, precision):
        if precision is None:
            precision = 2

        decimals = max(0, int(precision))
        step = precision - decimals

        if (step):
            num = math.floor(num / step) * step

        return float(("{0:." + str(decimals) + "f}").format(float(num)))

    def changePrice(self, first, input):
        changeObj = self.isChange(input)
        first = float(first)

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
                    "sign": sign, "percent": True}
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

    def referenceBalance(self, balance, quantity):
        if self.isPercent(quantity):
            diff = float(quantity.strip("%"))
            return balance * (diff / 100)
        else:
            return float(quantity)

    def logResponse(self, requestName, json):
        self.isErrorResponse(requestName, json)

    def isErrorResponse(self, requestName, json):
        if json.get("error"):
            self.logger.error("Error received after sending %s: %s",
                              requestName, json)
            return True
        else:
            self.logger.debug(
                "Response received after sending %s: %s", requestName, json)
            return False
