# carRoute Deployment Guide

---

## Overview

Deploy the **carRoute** Flask app on two web servers (`web-01`, `web-02`) using **Gunicorn** and **Nginx**. Use **HAProxy** on a third server (`lb-01`) to load balance traffic between them.

---

## Deployment on Web Servers (`web-01` & `web-02`)

<details>
<summary><strong>Step 1: Install Dependencies</strong></summary>

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip nginx -y
```
</details>

<details>
<summary><strong>Step 2: Set Up Application</strong></summary>

```bash
cd /home/ubuntu/
git clone <your-git-repo-url> carRoute
cd carRoute
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
</details>

<details>
<summary><strong>Step 3: Test Gunicorn</strong></summary>

```bash
venv/bin/gunicorn --bind 127.0.0.1:8000 app:app
```
Visit [http://localhost:8000](http://localhost:8000) to check the app.
</details>

<details>
<summary><strong>Step 4: Configure Gunicorn as a Service</strong></summary>

Create `/etc/systemd/system/carRoute.service`:
```ini
[Unit]
Description=Gunicorn instance to serve carRoute
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/carRoute
Environment="PATH=/home/ubuntu/carRoute/venv/bin"
ExecStart=/home/ubuntu/carRoute/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app

[Install]
WantedBy=multi-user.target
```
Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl start carRoute
sudo systemctl enable carRoute
```
</details>

<details>
<summary><strong>Step 5: Configure Nginx</strong></summary>

Create `/etc/nginx/sites-available/carRoute`:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable and reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/carRoute /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```
</details>

---

## Load Balancer Setup (`lb-01`)

Edit `/etc/haproxy/haproxy.cfg`:
```haproxy
frontend http_front
    bind *:80
    default_backend carroute_servers

backend carroute_servers
    balance roundrobin
    option httpchk GET /
    server web01 <web-01-ip>:80 check
    server web02 <web-02-ip>:80 check
```
Replace `<web-01-ip>` and `<web-02-ip>` with your actual IPs.

Reload HAProxy:
```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
sudo systemctl restart haproxy
```

---

## Testing

- Access the app via the load balancer:
  ```bash
  curl http://<lb-01-ip>
  ```
- Refresh several times to see load balancing in action.
- Check logs on web servers and HAProxy for confirmation.

---

## Secrets Handling (Recommended)

- Store API keys as environment variables on each web server.
- Access them in Flask via `os.getenv()`.
- **Never** hardcode secrets in code or configs.

---

## Credits

- [Flask](https://flask.palletsprojects.com/)
- [HAProxy](https://www.haproxy.org/)
- [Nginx](https://www.nginx.com/)
- Gemini API
- Cloudflare

---

## Author

**Bode Murairi**  
[b.murairi@alustudent.com]  


---

<sub>I am always available for feedback</sub>
