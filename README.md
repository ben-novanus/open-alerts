# Open-Alerts

This is BETA software for testing! I am not responsible for any losses incurred.

This is a daemon that accepts alerts from TradingView using webhooks and sends commands to an exchange using GOAT Alerts syntax or AutoView syntax

### Requirements
Python 3.5+
Python websockets
Python requests

### Setup
Ubuntu 18.04:
```sh
sudo apt-get install python3-websockets python3-requests
```

### nginx
It is recommended to use nginx with a proxy pass for open-alerts. Once this is setup up it is easy to use certbot to secure the server with ssl.
Here is an example proxy pass config:
```
server {
    listen 80;
    listen [::]:80;

    server_name example.com;

    root /var/www/example.com;
    index index.html;

    location / {
           try_files $uri $uri/ =404;
    }

    location /alerts/ {
        allow 52.89.214.238;
        allow 34.212.75.30;
        allow 54.218.53.128;
        allow 52.32.178.7;
        deny all;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass http://localhost:8001;
    }
}
```
Set the Webhook URL to "http//example.com/alerts/" on the Trading View alert (The trailing slash is important)

### systemd
Here is an example of a startup script
```
[Unit]
Description=Open-Alerts Daemon
After= network.target

[Service]
WorkingDirectory=/root/open-alerts/open-alerts
ExecStart=/usr/bin/python3 main.py
RestartSec=3
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Exchange Permissions
For ByBit the API key must have the following permissions
```
Key Permission: Active Order and Positions
```
For Deribit the API key must have the following permissions
```
account: read
block_trade: none
custody: none
trade: read_write
wallet: none
```

### Syntax Examples
Syntax examples can be found [here](https://github.com/draggy/open-alerts/wiki/Syntax-Examples).

### Syntax Notes
When using GOAT syntax you must include which symbol the alert is for. You will need to add a new line to the top section of the alert

#### ByBit (btcusd, ethusd, eosusd, xrpusd)
```
instrument = btcusd
```

#### Deribit (btc-perpetual, eth-perpetual)
```
instrument = btc-perpetual
```


When using AutoView syntax you must use the same account (a=) for every line (except delay=)


You can use multiple account names for an alert, each separated by a comma. Or you can use a wildcard to apply the alert to all accounts

#### GOAT
```
account = account1,account2,account3
account = *
```
#### AutoView
```
a=account1,account2,account3
a=*
```
