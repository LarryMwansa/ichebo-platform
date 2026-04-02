#!/bin/bash
# ICS Manual Deploy Script
# Run on VPS: ./deploy.sh
# Requires: git, python venv at ~/ics/venv, gunicorn systemd service named 'ics'

set -e  # Stop on any error

echo "=== ICS Deploy starting ==="

# 1. Pull latest code
echo "Pulling from GitHub..."
git pull origin main

# 2. Activate virtualenv
source venv/bin/activate

# 3. Install any new dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt --quiet

# 4. Run migrations
echo "Running migrations..."
cd backend
python manage.py migrate --noinput

# 5. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
cd ..

# 6. Restart Gunicorn
echo "Restarting Gunicorn..."
sudo systemctl restart ics

echo "=== Deploy complete ==="
