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
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev -y
```
</details>

<details>
<summary><strong>Step 2: Set Up Application</strong></summary>

```bash
cd /home/ubuntu/
git clone https://github.com/BodeMurairi2/carRoute.git
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
    server web01 54.211.222.161:80 check
    server web02 44.203.73.117:80 check
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
  curl http://13.221.249.199/
  ```
- Refresh several times to see load balancing in action.
- Check logs on web servers and HAProxy for confirmation.
- I added an header on the request so whenever a request the loadbalancer, I could view where the loadbalancer sent the traffic.

---

## Secrets Handling (Recommended)

- Store API keys as environment variables on each web server.
- Access them in Flask via `os.getenv()`.
- I used the SCP protocole to copy auth.env and config.env from my computer to my web-01 and web-02
- **Never** hardcode secrets in code or configs.

---
##
Application video: https://www.loom.com/share/f836d28a01f44afabae699badec32f04?sid=02ed1e8d-eecd-4e3a-885a-7cc3e2c89894
Application deploy on : Web-01: http://54.211.222.161/
                        Web-02: http://44.203.73.117/
Loadbalencer done and http redirect to https: http://13.221.249.199/
Note: enlightenment-lab.tech is not yet propagated. So, I could not proceed with the encryption with let's encrypt.

## Credits

- [Flask](https://flask.palletsprojects.com/)
- [HAProxy](https://www.haproxy.org/)
- [Nginx](https://www.nginx.com/)
- Google-generativeai with model gemini-2.5-flash
- Cloudflare R2 Bucket for storing each image
- Amazon AWS API via booto3, which is compatible to R2 Bucket for Cloudflare

---
## Challenges
- My servers used Python 3.8 version, an old version of Python, which created many dependency issues.
- I could not install Google Genai on my server. As a result, I rewrote my get_request() function using google-generativeai module.
- However, since it was an old Python version, Google-GenerativeAI 0.1 was installed by default each time I tried to install using pip
- I had to manually install Python 3.10 and specify Google-GenerativeAI version 0.3.2 to overcome this problem
- As I was building a Flask application, I needed a process manager, gunicorn. Setting up gunicorn to keep running app.py was another challenge
- Serving nginx for a Flask application was really hectic in many different ways.
- I believe I could have a better result using Docker to containerize my application and avoid modules and dependency issues.
- I learned a lot during this project and am open to any feedback and areas of improvement
## Author

**Bode Murairi**  
[b.murairi@alustudent.com]  


---

<sub>I am always available for feedback</sub>
