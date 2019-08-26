from exchanges.deribit import Deribit


class Account:
    def __init__(self, name, type, key, secret):
        self.name = name
        self.type = type
        self.key = key
        self.secret = secret

    def processAlert(self, alert):
        if self.type == "deribit":
            exchange = Deribit()
            exchange.processAlert(alert)
        elif self.type == "deribit-test":
            exchange = Deribit(True)
            exchange.processAlert(alert)
        elif self.type == "bitmex":
            print("Exchange " + self.type + " not yet implemented")
        elif self.type == "bitmex-test":
            print("Exchange " + self.type + " not yet implemented")
        elif self.type == "bybit":
            print("Exchange " + self.type + " not yet implemented")
        elif self.type == "bybit-test":
            print("Exchange " + self.type + " not yet implemented")
        else:
            print("Exchange " + self.type + " not yet implemented")
