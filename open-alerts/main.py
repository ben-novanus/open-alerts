from configparser import ConfigParser
from functools import partial
from http.server import HTTPServer
import logging
from handler import AlertRequestHandler
from models.account import Account


def main():
    config = ConfigParser(strict=False)
    config.read('config.ini')

    logger = logging.getLogger("main")
    logging.basicConfig(filename='main.log',
                        filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)

    print("starting handler")

    # Configure the handler
    valid_ips = ["52.89.214.238",
                 "34.212.75.30",
                 "54.218.53.128",
                 "52.32.178.7"]

    accounts = {}
    for section_name in config.sections():
        if (section_name.startswith("Account") and
            config.get(section_name, 'Name') and
            config.get(section_name, 'Type') and
            config.get(section_name, 'Key') and
                config.get(section_name, 'Secret')):
            account = Account(config.get(section_name, 'Name'),
                              config.get(section_name, 'Type'),
                              config.get(section_name, 'Key'),
                              config.get(section_name, 'Secret'))
            accounts[account.name] = account

    handler = partial(AlertRequestHandler, valid_ips, accounts)
    server_address = (config.get('Settings', 'Bind'),
                      config.getint('Settings', 'Port'))

    httpd = HTTPServer(server_address, handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
