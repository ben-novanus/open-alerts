from http.server import BaseHTTPRequestHandler
import logging
from models.alert import Alert


class AlertRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, valid_ips, accounts, *args, **keywords):
        self.logger = logging.getLogger("main")
        self.valid_ips = valid_ips
        self.accounts = accounts
        super().__init__(*args, **keywords)

    def do_GET(self):
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.client_address[0] not in self.valid_ips:
            self.logger.warning("Unauthorized IP address: %s",
                                self.client_address[0])
            self.send_response(401)
            self.end_headers()
        else:
            self.logger.debug("Received alert from IP address: %s",
                              self.client_address[0])

            self.send_response(200)
            self.end_headers()

            length = int(self.headers.get('Content-Length', 0))
            body = str(self.rfile.read(length))

            self.logger.debug("Body of alert: %s", body)

            if body.startswith('b\'', 0, 2) and body.endswith('\''):
                body = body[2:len(body) - 1]

                alert = Alert(body)
                if alert.accounts:
                    if alert.accounts[0] == "*":
                        for account in self.accounts:
                            account.processAlert(alert)
                    else:
                        for account in alert.accounts:
                            if account in self.accounts.keys():
                                self.accounts.get(account).processAlert(alert)
                            else:
                                self.logger.error(("Unable to find account with "
                                                   "name: %s"), account)
                else:
                    self.logger.error(("Unable to parse alert "
                                       "with body: %s"), body)
            else:
                self.logger.error("Invalid alert body received: %s", body)
