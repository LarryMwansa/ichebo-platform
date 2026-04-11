# Task 0.5 — VPS Production Setup Guide

**For:** Ubuntu 22.04 with PostgreSQL already installed  
**User:** `scepter`  
**App location:** `/home/scepter/ics/`  
**Domain:** `your-domain.com` (replace throughout)

---

## Pre-flight Checklist

Before you start, have ready:

- [ ] VPS SSH access (user: `scepter`)
- [ ] Domain name (e.g., `example.com`)
- [ ] Email for Let's Encrypt SSL
- [ ] PostgreSQL already running on the VPS
- [ ] Git repo URL (to clone the ICS app)
- [ ] A strong password for the PostgreSQL `ics_user` account

---

## Quick Start (automated)

If you prefer to run a single script:

```bash
ssh scepter@your-vps-ip
cd ~
# Download and run the setup script
wget https://raw.githubusercontent.com/your-repo/project_docs/0.5-task_vps-setup.sh
chmod +x 0.5-task_vps-setup.sh
./0.5-task_vps-setup.sh
```

Then skip to **[Step 11: Setup SSL](#step-11-setup-ssl-with-lets-encrypt)** below.

---

## Step-by-Step Manual Setup

### Step 1: SSH into your VPS

```bash
ssh scepter@your-vps-ip
```

### Step 2: Verify prerequisites

```bash
# Check Python
python3 --version

# Check PostgreSQL
psql --version

# Check if git is installed
git --version
# If not: sudo apt install git
```

### Step 3: Clone the ICS repo

```bash
cd ~
git clone <YOUR_REPO_URL> ics
cd ics
```

### Step 4: Create `.env` file with production secrets

```bash
# Generate a secure SECRET_KEY
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_NAME=ics_db
DB_USER=ics_user
DB_PASSWORD=choose-a-strong-password-here
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://your-domain.com
EOF
```

**Edit the file and fill in your values:**

```bash
nano .env
# Update:
#   - ALLOWED_HOSTS: your actual domain
#   - DB_PASSWORD: a strong password (20+ chars, mix of upper/lower/numbers/symbols)
#   - CORS_ALLOWED_ORIGINS: your actual domain
```

**Keep this file secret!** Make it readable only by you:

```bash
chmod 600 .env
```

### Step 5: Create Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 6: Setup PostgreSQL database and user

Load your `.env` vars:

```bash
export $(cat .env | grep -v '^#' | xargs)
```

Create the PostgreSQL user and database:

```bash
sudo -u postgres psql << SQL
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET default_transaction_deferrable TO on;
ALTER ROLE $DB_USER SET timezone TO 'UTC';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
SQL
```

Verify the connection:

```bash
psql -h localhost -U ics_user -d ics_db -c "SELECT version();"
# Enter the password when prompted
```

### Step 7: Run Django migrations

```bash
cd ~/ics
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=ics_project.settings.production
python manage.py migrate
```

Expected output: `Running migrations: ... (1 applied)`

### Step 8: Collect static files

```bash
python manage.py collectstatic --noinput
```

Expected output: `... static files copied to '.../staticfiles'`

### Step 9: Create system directories

```bash
sudo mkdir -p /var/log/gunicorn /var/log/ics /var/cache/ics
sudo chown www-data:www-data /var/cache/ics /var/log/ics /var/log/gunicorn
```

### Step 10: Install and configure Nginx

Install Nginx:

```bash
sudo apt update
sudo apt install -y nginx
```

Create the Nginx config:

```bash
sudo tee /etc/nginx/sites-available/ics > /dev/null << 'NGINX'
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (certbot will auto-populate these)
    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Static files (served directly by Nginx)
    location /static/ {
        alias /home/scepter/ics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Everything else → Gunicorn on :8001
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
NGINX
```

**Replace `your-domain.com` with your actual domain:**

```bash
sudo sed -i 's/your-domain.com/your-actual-domain.com/g' /etc/nginx/sites-available/ics
```

Enable the site and test:

```bash
sudo unlink /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/ics /etc/nginx/sites-enabled/
sudo nginx -t
# Expected: "syntax is ok"

sudo systemctl restart nginx
```

### Step 11: Setup SSL with Let's Encrypt

Install certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

Get an SSL certificate (certbot auto-updates the Nginx config):

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

When prompted:
- Enter your email
- Accept the terms
- Choose "Redirect" (automatically redirect HTTP → HTTPS)

Verify SSL:

```bash
curl -I https://your-domain.com
# Should see: HTTP/2 200
```

### Step 12: Start Gunicorn (manual test)

```bash
cd ~/ics
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=ics_project.settings.production
gunicorn ics_project.wsgi:application -c gunicorn.conf.py
```

You should see:

```
[INFO] Starting gunicorn 25.3.0
[INFO] Listening at: http://127.0.0.1:8001 (12345)
[INFO] Using worker: sync
[INFO] Booting worker with pid: 12346
```

**Test in another terminal:**

```bash
curl -I https://your-domain.com/
# Should see: HTTP/2 200

curl -I https://your-domain.com/api/paraclete/health/
# Should see: {"status": "ok", "app": "paraclete"}
```

Press `Ctrl+C` to stop the manual Gunicorn.

### Step 13: Setup Gunicorn as a systemd service (auto-start)

This makes Gunicorn start automatically on reboot and restart if it crashes.

Copy the service file:

```bash
sudo cp ~/ics/project_docs/0.5-task_gunicorn-systemd.service /etc/systemd/system/ics-gunicorn.service
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ics-gunicorn
sudo systemctl start ics-gunicorn
```

Check status:

```bash
sudo systemctl status ics-gunicorn
# Should show "active (running)"

# View logs
sudo journalctl -u ics-gunicorn -n 50 --follow
```

---

## Verification Checklist

After setup, verify everything works:

```bash
# Check Nginx is running
sudo systemctl status nginx

# Check Gunicorn is running
sudo systemctl status ics-gunicorn

# Test HTTP → HTTPS redirect
curl -I http://your-domain.com
# Should redirect to https://...

# Test the app is accessible
curl https://your-domain.com
# Should return HTML dashboard page

# Test API health
curl https://your-domain.com/api/paraclete/health/
# Should return: {"status": "ok", "app": "paraclete"}

# Check static files are served by Nginx
curl -I https://your-domain.com/static/css/variables.css
# Should return 200 (not proxied to Gunicorn)

# Check logs
tail -f /var/log/gunicorn/ics_access.log
tail -f /var/log/ics/django.log
```

---

## Troubleshooting

### Gunicorn won't start

```bash
sudo journalctl -u ics-gunicorn -n 50
# Look for error messages
```

Common issues:
- `ModuleNotFoundError`: Activate venv: `source /home/scepter/ics/.venv/bin/activate`
- `TemplateNotFound`: Run `python manage.py collectstatic`
- `Connection refused (DB)`: Check PostgreSQL is running: `sudo systemctl status postgresql`

### Nginx 502 Bad Gateway

Gunicorn is not running or not listening on `:8001`:

```bash
sudo systemctl restart ics-gunicorn
sudo lsof -i :8001
# Should show gunicorn listening
```

### SSL certificate errors

```bash
# Renew early (they auto-renew, but you can test)
sudo certbot renew --dry-run

# Check expiration
sudo certbot certificates
```

### Database connection errors

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Verify connection string
psql -h localhost -U ics_user -d ics_db -c "SELECT 1;"
# Enter your DB_PASSWORD when prompted
```

---

## Maintenance

### Deploy code updates

```bash
cd ~/ics
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart ics-gunicorn
```

### View logs

```bash
# Gunicorn access log
tail -f /var/log/gunicorn/ics_access.log

# Django error log
tail -f /var/log/ics/django.log

# Systemd log
sudo journalctl -u ics-gunicorn -n 100 --follow
```

### Restart services

```bash
sudo systemctl restart ics-gunicorn
sudo systemctl restart nginx
```

---

## Production notes

- **`DEBUG=False`** in production — any 500 error won't show details (good for security)
- **HTTPS enforced** — all traffic redirects to HTTPS via Nginx
- **Static files** — served by Nginx directly, not by Gunicorn (fast)
- **Database** — PostgreSQL is much more robust than SQLite for production
- **Logs** — check `/var/log/ics/django.log` regularly for errors
- **Backups** — backup your PostgreSQL database regularly!

---

**Questions?** Check `DJANGO_SETTINGS_MODULE=ics_project.settings.production` and review `ics_project/settings/production.py` for what each setting does.
