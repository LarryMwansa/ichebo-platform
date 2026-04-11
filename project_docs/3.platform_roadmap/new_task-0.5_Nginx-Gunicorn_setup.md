 ---
  Updated Task 0.5 — Nginx + Gunicorn (production)

  Files to create:

  gunicorn.conf.py (unchanged from roadmap):
  bind = "127.0.0.1:8001"
  workers = 3
  timeout = 120
  accesslog = "/var/log/gunicorn/ics_access.log"
  errorlog = "/var/log/gunicorn/ics_error.log"

  /etc/nginx/sites-available/ics (UPDATED for SSR Django):

  # Redirect HTTP → HTTPS
  server {
      listen 80;
      server_name your-domain.com;
      return 301 https://$host$request_uri;
  }

  server {
      listen 443 ssl;
      server_name your-domain.com;

      # certbot will auto-fill these:
      ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

      # Static files (served by Nginx, not Gunicorn)
      location /static/ {
          alias /home/ics/ics/staticfiles/;
          expires 30d;
          add_header Cache-Control "public";
      }

      # Everything else → Gunicorn
      location / {
          proxy_pass http://127.0.0.1:8001;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }

  Deployment steps (updated):

  # 1. Create log/cache directories
  sudo mkdir -p /var/log/gunicorn /var/log/ics /var/cache/ics
  sudo chown www-data:www-data /var/cache/ics
  sudo chown $USER:$USER /var/log/gunicorn /var/log/ics

  # 2. Install dependencies
  pip install -r requirements.txt

  # 3. Collect static files (must use production settings)
  export DJANGO_SETTINGS_MODULE=ics_project.settings.production
  python manage.py collectstatic --no-input

  # 4. Run migrations (PostgreSQL)
  python manage.py migrate

  # 5. Copy gunicorn.conf.py
  cp gunicorn.conf.py ~/ics/

  # 6. Setup Nginx
  sudo cp /etc/nginx/sites-available/ics /etc/nginx/sites-available/ics.backup
  # (edit /etc/nginx/sites-available/ics with the config above)
  sudo ln -s /etc/nginx/sites-available/ics /etc/nginx/sites-enabled/
  sudo nginx -t
  sudo systemctl restart nginx

  # 7. Setup SSL (Let's Encrypt)
  sudo apt install certbot python3-certbot-nginx
  sudo certbot --nginx -d your-domain.com

  # 8. Start Gunicorn
  export DJANGO_SETTINGS_MODULE=ics_project.settings.production
  gunicorn ics_project.wsgi:application -c gunicorn.conf.py

  # 9. Test
  curl https://your-domain.com/api/paraclete/health/
  # Expected: {"status": "ok", "app": "paraclete"}

  Key changes from roadmap:

  ┌────────────────────────┬──────────────────────────────────────┬───────────────────────────────────────────────────────┐
  │          Item          │               Roadmap                │                          Now                          │
  ├────────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────────────────┤
  │ Nginx location /       │ Routes to /frontend/index.html (SPA) │ Routes to Gunicorn (SSR)                              │
  ├────────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────────────────┤
  │ DJANGO_SETTINGS_MODULE │ Not mentioned                        │ Must export production to enable HTTPS/security flags │
  ├────────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────────────────┤
  │ Cache dir              │ Not created                          │ /var/cache/ics must exist and be writable by www-data │
  ├────────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────────────────┤
  │ Log dirs               │ Nginx + Gunicorn logs mentioned      │ Add /var/log/ics/ for Django errors                   │
  ├────────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────────────────┤
  │ collectstatic          │ Not in roadmap                       │ Must run before starting Gunicorn                     │
  ├────────────────────────┼──────────────────────────────────────┼───────────────────────────────────────────────────────┤
  │ migrations             │ Not in roadmap                       │ Must run once after DB is created                     │
  └────────────────────────┴──────────────────────────────────────┴───────────────────────────────────────────────────────┘