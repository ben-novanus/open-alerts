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

    def do_POST(self):
        if self.client_address[0] not in self.valid_ips:
            self.logger.debug("Unauthorized IP address: %s",
                              self.client_address[0])
            self.send_response(401)
        else:
            length = int(self.headers.get('Content-Length', 0))
            body = str(self.rfile.read(length))

            if body.startswith('b\'', 0, 2) and body.endswith('\''):
                body = body[2:len(body) - 1]

                alert = Alert(body)
                self.accounts.get(alert.account).processAlert(alert)

                # self.send_response(200)
            else:
                self.logger.error("Invalid alert body received: %s", body)
