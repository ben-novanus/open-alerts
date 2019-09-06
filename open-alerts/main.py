from configparser import ConfigParser
from functools import partial
from http.server import HTTPServer
from socketserver import ThreadingMixIn
import logging
import sys
from handler import AlertRequestHandler
from models.account import Account


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


def main():
    print("\nStarting up")

    config = ConfigParser(strict=False)
    config.read("config.ini")

    logger = logging.getLogger("main")
    logging.basicConfig(filename="main.log",
                        filemode="w",
                        format="%(asctime)s - %(name)s - \
%(levelname)s - %(message)s")
    if config.get("Settings", "Logging"):
        logger.setLevel(config.get("Settings", "Logging"))
    else:
        logger.setLevel(logging.ERROR)

    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Unhandled exception", exc_info=(
            exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_unhandled_exception

    # Configure the handler
    valid_ips = ["127.0.0.1",
                 "52.89.214.238",
                 "34.212.75.30",
                 "54.218.53.128",
                 "52.32.178.7"]

    logger.info("parsing config")
    accounts = {}
    for section_name in config.sections():
        if (section_name.startswith("Account") and
            config.get(section_name, "Name") and
            config.get(section_name, "Type") and
            config.get(section_name, "Key") and
                config.get(section_name, "Secret")):
            account = Account(config.get(section_name, "Name"),
                              config.get(section_name, "Type"),
                              config.get(section_name, "Key"),
                              config.get(section_name, "Secret"))
            accounts[account.name] = account

    logger.info("starting handler")
    handler = partial(AlertRequestHandler, valid_ips, accounts)
    server_address = (config.get("Settings", "Bind"),
                      config.getint("Settings", "Port"))

    httpd = ThreadedHTTPServer(server_address, handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Shutting Down")


if __name__ == "__main__":
    main()
