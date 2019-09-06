# Open-Alerts

This is BETA software for testing! I am not responsible for any losses incurred.

This is a daemon that accepts alerts from tradingview using webhooks and sends commands to the proper exchange using GOAT Alerts syntax (Soon to support AutoView syntax)

### Requirements
Python 3.5+
Python websockets

### Setup
Ubuntu 18.04:
```sh
sudo apt-get install python3-websockets
```

### nginx
It is recommended to use nginx with a proxy pass for open-alerts. Once this is setup up is easy to use certbot to secure the server with ssl.
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

    location /alerts/test/ {
        allow 52.89.214.238;
        allow 34.212.75.30;
        allow 54.218.53.128;
        allow 52.32.178.7;
        deny all;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass http://localhost:8002;
    }
}
```

### systemd
Here is an example of a startup script
```
[Unit]
Description=Open-Alerts Daemon
After= network.target

[Service]
WorkingDirectory=/root/open-alerts/open-alerts
ExecStart=/usr/bin/python3 main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
