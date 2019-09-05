import logging
from exchanges.deribit import Deribit


class Account:
    def __init__(self, name, type, key, secret):
        self.logger = logging.getLogger('main')
        self.name = name
        self.type = type
        self.key = key
        self.secret = secret

    def processAlert(self, alert):
        if self.type == "deribit":
            exchange = Deribit(self.key, self.secret)
            exchange.processAlert(alert)
        elif self.type == "deribit-test":
            exchange = Deribit(self.key, self.secret, True)
            exchange.processAlert(alert)
        elif self.type == "bitmex":
            self.logger.error("Exchange %s not yet implemented", self.type)
        elif self.type == "bitmex-test":
            self.logger.error("Exchange %s not yet implemented", self.type)
        elif self.type == "bybit":
            self.logger.error("Exchange %s not yet implemented", self.type)
        elif self.type == "bybit-test":
            self.logger.error("Exchange %s not yet implemented", self.type)
        else:
            self.logger.error("Exchange %s not valid", self.type)
