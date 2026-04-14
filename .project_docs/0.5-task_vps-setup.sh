#!/bin/bash
# Task 0.5 — VPS Production Setup (Ubuntu 22.04)
# Usage: Run this on your VPS as the scepter user
# chmod +x 0.5-task_vps-setup.sh && ./0.5-task_vps-setup.sh

set -e  # exit on error

echo "=========================================="
echo "ICS Platform — Task 0.5 VPS Setup"
echo "=========================================="

# ── Step 1: Verify prerequisites ──────────────────────────────────────────

echo ""
echo "Step 1: Checking prerequisites..."

# Check if running as scepter
if [ "$(whoami)" != "scepter" ]; then
    echo "ERROR: Must run as scepter user. Run: ssh scepter@your-vps"
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "ERROR: PostgreSQL not found. Install with: sudo apt install postgresql postgresql-contrib"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Install with: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "✓ Prerequisites OK (PostgreSQL, Python3 found)"

# ── Step 2: Clone repo (if not already cloned) ────────────────────────────

echo ""
echo "Step 2: Setting up app directory..."

if [ ! -d "$HOME/ics" ]; then
    echo "Cloning repo to $HOME/ics..."
    cd $HOME
    git clone <REPO_URL> ics
    cd ics
else
    echo "✓ $HOME/ics already exists (assuming already cloned)"
    cd $HOME/ics
fi

echo "✓ App directory ready at: $HOME/ics"

# ── Step 3: Create .env file ──────────────────────────────────────────────

echo ""
echo "Step 3: Creating .env file..."

if [ -f ".env" ]; then
    echo "⚠ .env already exists. Skipping (to preserve secrets)."
else
    # Generate a secure SECRET_KEY
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=<YOUR_DOMAIN>,www.<YOUR_DOMAIN>
DB_NAME=ics_db
DB_USER=ics_user
DB_PASSWORD=<YOUR_POSTGRES_PASSWORD>
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://<YOUR_DOMAIN>
EOF

    echo "Created .env file. Please edit with your values:"
    echo "  - Replace <YOUR_DOMAIN> with your domain"
    echo "  - Replace <YOUR_POSTGRES_PASSWORD> with a strong password"
    echo ""
    echo "Edit: $HOME/ics/.env"
    exit 0  # User must edit .env before continuing
fi

# ── Step 4: Create Python virtual environment ─────────────────────────────

echo ""
echo "Step 4: Setting up Python virtual environment..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo "✓ Dependencies installed"

# ── Step 5: Setup PostgreSQL database ─────────────────────────────────────

echo ""
echo "Step 5: Setting up PostgreSQL..."

# Load .env
export $(cat .env | grep -v '^#' | xargs)

# Check if DB user exists; if not, create
DB_USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'")

if [ -z "$DB_USER_EXISTS" ]; then
    echo "Creating PostgreSQL user: $DB_USER"
    sudo -u postgres psql << SQL
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET default_transaction_deferrable TO on;
ALTER ROLE $DB_USER SET timezone TO 'UTC';
SQL
    echo "✓ PostgreSQL user created"
else
    echo "✓ PostgreSQL user already exists"
fi

# Check if DB exists; if not, create
DB_EXISTS=$(sudo -u postgres psql -lt | grep -w $DB_NAME)

if [ -z "$DB_EXISTS" ]; then
    echo "Creating PostgreSQL database: $DB_NAME"
    sudo -u postgres createdb --owner=$DB_USER $DB_NAME
    echo "✓ PostgreSQL database created"
else
    echo "✓ PostgreSQL database already exists"
fi

# ── Step 6: Run Django migrations ─────────────────────────────────────────

echo ""
echo "Step 6: Running Django migrations..."

export DJANGO_SETTINGS_MODULE=ics_project.settings.production
python manage.py migrate
echo "✓ Migrations applied"

# ── Step 7: Collect static files ──────────────────────────────────────────

echo ""
echo "Step 7: Collecting static files..."

python manage.py collectstatic --noinput
echo "✓ Static files collected to: $(pwd)/staticfiles"

# ── Step 8: Create log and cache directories ──────────────────────────────

echo ""
echo "Step 8: Creating system directories..."

sudo mkdir -p /var/log/gunicorn /var/log/ics /var/cache/ics
sudo chown www-data:www-data /var/cache/ics /var/log/ics
sudo chown www-data:www-data /var/log/gunicorn
echo "✓ Directories created and permissions set"

# ── Step 9: Setup Nginx ───────────────────────────────────────────────────

echo ""
echo "Step 9: Setting up Nginx..."

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

# Create Nginx config (HTTP only for now; certbot will add HTTPS)
sudo tee /etc/nginx/sites-available/ics > /dev/null << 'NGINX'
# Redirect HTTP to HTTPS (after certbot sets up SSL)
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS server (certbot will auto-configure)
server {
    listen 443 ssl http2;
    server_name _;

    # SSL certs (certbot will fill these in)
    ssl_certificate     /etc/letsencrypt/live/DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN/privkey.pem;

    # Static files
    location /static/ {
        alias /home/scepter/ics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Everything else → Gunicorn
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

echo "⚠ Nginx config created at /etc/nginx/sites-available/ics"
echo "  Replace 'DOMAIN' with your actual domain before enabling"

# ── Step 10: Test and enable Nginx ────────────────────────────────────────

echo ""
echo "Step 10: Enabling Nginx..."

# Disable default site
sudo unlink /etc/nginx/sites-enabled/default 2>/dev/null || true

# Enable ics site
sudo ln -sf /etc/nginx/sites-available/ics /etc/nginx/sites-enabled/

# Test config
if sudo nginx -t; then
    echo "✓ Nginx config test passed"
    sudo systemctl restart nginx
    echo "✓ Nginx restarted"
else
    echo "ERROR: Nginx config test failed. Fix /etc/nginx/sites-available/ics"
    exit 1
fi

# ── Summary ───────────────────────────────────────────────────────────────

echo ""
echo "=========================================="
echo "✓ Step 1-10 Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Update Nginx config with your domain:"
echo "   sudo nano /etc/nginx/sites-available/ics"
echo "   (Replace 'DOMAIN' with your actual domain, e.g., example.com)"
echo ""
echo "2. Setup SSL with Let's Encrypt:"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d your-domain.com"
echo ""
echo "3. Start Gunicorn (test manually first):"
echo "   cd ~/ics"
echo "   source .venv/bin/activate"
echo "   export DJANGO_SETTINGS_MODULE=ics_project.settings.production"
echo "   gunicorn ics_project.wsgi:application -c gunicorn.conf.py"
echo ""
echo "4. (Optional) Setup systemd service to auto-start Gunicorn"
echo "   See: project_docs/0.5-task_gunicorn-systemd.service"
echo ""
