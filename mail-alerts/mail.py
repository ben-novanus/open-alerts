import poplib
from email.parser import BytesParser, Parser
from email.policy import default
from models.alert import Alert


class Email:
    def __init__(self, server, port, tls, user, password):
        self.server = server
        self.port = port
        self.tls = tls
        self.user = user
        self.password = password

    def processMail(self):
        try:
            if self.tls == "1":
                pop3 = poplib.POP3_SSL(self.server, self.port)
            else:
                pop3 = poplib.POP3(self.server, self.port)

            pop3.user(self.user)
            pop3.pass_(self.password)
        except:
            print("Failed to connect to server.")

        deleted = 0
        alerts = []

        try:
            msgCount = len(pop3.list()[1])
            for i in range(msgCount):
                msgIndex = i + 1
                top = pop3.top(msgIndex, 0)

                message = '\n'.join(map(bytes.decode, top[1]))

                headers = Parser(policy=default).parsestr(message)

                if headers['from'] == "noreply@tradingview.com":
                    alert = Alert()
                    alert.parseSubject(headers['subject'])
                    alerts.append(alert)
                    # pop3.dele(msgIndex)

        except:
            pop3.rset()
            deleted = 0
            print("ERROR DURING PROCESSING - %d messages deleted. %d messages left on server" %
                  (deleted, msgCount - deleted))
        finally:
            pop3.quit()
            print("%d messages deleted. %d messages left on server" %
                  (deleted, msgCount - deleted))
            return alerts
