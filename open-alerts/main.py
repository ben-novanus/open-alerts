from configparser import ConfigParser
from functools import partial
from http.server import HTTPServer
from socketserver import ThreadingMixIn
import logging
from pytz import timezone
from datetime import datetime
import sys
from handler import AlertRequestHandler
from models.account import Account


class TimeZoneFormatter(logging.Formatter):
    def __init__(self, timezone, *args, **keywords):
        self.timezone = timezone
        super().__init__(*args, **keywords)

    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        tz = timezone(self.timezone)
        dt = tz.localize(dt)
        return dt.astimezone(tz)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            try:
                s = dt.isoformat(timespec="milliseconds")
            except TypeError:
                s = dt.isoformat()
        return s


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


def main():
    print("\nStarting up")

    config = ConfigParser(strict=False)
    config.read("config.ini")

    # Setup the logger
    logger = logging.getLogger("main")
    logger.setLevel(config.get("Logging", "Level"))

    fh = logging.FileHandler(filename=config.get("Logging", "File"), mode="a")

    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    dateFormat = "%Y-%m-%d %H:%M:%S"
    if config.has_option("Logging", "TimeZone"):
        formatter = TimeZoneFormatter(
            config.get("Logging", "TimeZone"),
            fmt=format,
            datefmt=dateFormat
        )
    else:
        formatter = logging.Formatter(
            fmt=format,
            datefmt=dateFormat
        )
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Unhandled exception", exc_info=(
            exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_unhandled_exception

    logger.info("Starting up")

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
    server_address = (config.get("Server", "Bind"),
                      config.getint("Server", "Port"))

    httpd = ThreadedHTTPServer(server_address, handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logger.info("Shutting Down")

    print("Shutting Down")


if __name__ == "__main__":
    main()
