# ICS Platform — Production Engineering Guide

> **For:** Chizola — first production deployment reference
> **Date:** 2026-04-12
> **Context:** Hetzner VPS, Ubuntu 22.04, Django 4.2, PostgreSQL, Nginx, Gunicorn
> **Scope:** Everything you need to know to run this project professionally —
> from your laptop to a live, secure, maintainable production server.

---

## How to read this document

You do not need to understand everything here before you start. Read it once to get
the lay of the land, then come back to each section when you reach that stage of the
build. Think of it as a map, not a manual.

The sections are ordered the way the work actually happens:

1. Before you touch the server — set up your tools and accounts
2. The server itself — first-time Hetzner setup
3. Code and version control — how code moves from your laptop to the server
4. The development loop — how you work day to day
5. Secrets and environment — how to handle passwords safely
6. Backups — how to avoid losing everything
7. Monitoring — how to know when something breaks
8. Deploying changes — how to push new code safely
9. Standard documentation — what files a production project must have
10. Maintenance — the ongoing work of running a server

---

## Part 1 — Before You Touch the Server

### 1.1 Accounts you need

Before provisioning a server, create or confirm you have the following:

| Account | Purpose | Where |
|---------|---------|-------|
| Hetzner Cloud account | Your VPS lives here | cloud.hetzner.com |
| Domain registrar account | DNS for your-domain.com | wherever you bought the domain |
| GitHub account | Code repository | github.com |
| Email for alerts | Server sends error emails here | your existing email is fine |

### 1.2 Tools on your local machine

You work from your laptop via VS Code with the Remote-SSH extension (already your
pattern). You also need these tools locally:

```bash
# Check if you already have these:
git --version          # should be 2.x or higher
ssh -V                 # should be OpenSSH 8.x or higher
python3 --version      # for running local tests
```

If you are on Windows, use WSL2 (Windows Subsystem for Linux). Everything in this
guide assumes a Unix-like terminal (Linux, macOS, or WSL2).

### 1.3 SSH key setup (critical — do this first)

An SSH key is how you log into your server without a password. It is more secure
than a password and required for automated deployments.

```bash
# On your LOCAL machine (laptop):

# 1. Generate a key pair (if you don't already have one)
ssh-keygen -t ed25519 -C "your-email@example.com"
# Accept the default location (~/.ssh/id_ed25519)
# Set a passphrase — write it down somewhere safe

# 2. View your public key (this is safe to share)
cat ~/.ssh/id_ed25519.pub
# It will look like: ssh-ed25519 AAAA... your-email@example.com

# 3. Copy the output — you will paste it into Hetzner when creating the server
```

**Keep your private key (`~/.ssh/id_ed25519`) on your laptop only. Never upload it
anywhere. Never paste it into any website. The public key (`.pub`) is what goes on
the server.**

---

## Part 2 — Hetzner VPS Setup

### 2.1 Choosing a server

For ICS MVP, a Hetzner CX22 or CX32 is appropriate:

| Model | vCPU | RAM | Storage | Approx cost |
|-------|------|-----|---------|-------------|
| CX22  | 2    | 4 GB | 40 GB SSD | ~€4.90/month |
| CX32  | 4    | 8 GB | 80 GB SSD | ~€9.90/month |

Start with CX22. You can resize later without data loss in Hetzner. Choose the
**Nuremberg or Falkenstein** data centre (Europe) or **Ashburn** (USA) — pick the
one closest to your primary users.

Choose **Ubuntu 22.04 LTS** as the operating system.

### 2.2 Creating the server

In the Hetzner Cloud console:

1. Click **Create Server**
2. Select: Ubuntu 22.04
3. Select: your server type (CX22 to start)
4. Under **SSH Keys**: paste your public key from Step 1.3 and name it (e.g. "my-laptop")
5. Under **Networking**: enable a public IPv4 address
6. Name your server: `ics-production`
7. Click **Create & Buy Now**

You will receive an IP address (e.g. `95.216.x.x`). This is your server's address.

### 2.3 First login

```bash
# From your laptop — replace with your actual IP
ssh root@95.216.x.x

# If it asks "Are you sure you want to continue connecting?" — type yes
# You should be logged in as root
```

**You are now on the server as the root user.** Root has unlimited power on this
machine. The first thing you do is create a safer user and disable direct root login.

### 2.4 First-time server hardening

Run these commands once, immediately after your first login:

```bash
# 1. Update all system packages
apt update && apt upgrade -y

# 2. Create the ICS deploy user
adduser ics
# Set a strong password — write it down
# Fill in the prompts or just press Enter to skip

# 3. Give ics user sudo access
usermod -aG sudo ics

# 4. Copy your SSH key to the ics user
mkdir -p /home/ics/.ssh
cp /root/.ssh/authorized_keys /home/ics/.ssh/
chown -R ics:ics /home/ics/.ssh
chmod 700 /home/ics/.ssh
chmod 600 /home/ics/.ssh/authorized_keys

# 5. Test that you can log in as ics BEFORE disabling root
# Open a new terminal window on your laptop and try:
# ssh ics@95.216.x.x
# If it works, continue below

# 6. Disable root SSH login (back in the root session)
nano /etc/ssh/sshd_config
# Find the line: PermitRootLogin yes
# Change it to: PermitRootLogin no
# Find the line: PasswordAuthentication yes
# Change it to: PasswordAuthentication no
# Save (Ctrl+O, Enter) and exit (Ctrl+X)

# 7. Restart SSH to apply changes
systemctl restart sshd

# 8. Set up the firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
# When asked "Command may disrupt existing ssh sessions. Proceed?" — type y

# 9. Verify firewall status
ufw status
# Should show: OpenSSH ALLOW Anywhere, Nginx Full ALLOW Anywhere
```

From now on, you SSH as `ics`, not `root`:

```bash
ssh ics@95.216.x.x
```

### 2.5 Point your domain to the server

In your domain registrar (wherever you bought your domain), create an **A record**:

```
Type:  A
Name:  @        (or your subdomain, e.g. app)
Value: 95.216.x.x   (your server IP)
TTL:   3600
```

If you want `www.your-domain.com` to also work:

```
Type:  A
Name:  www
Value: 95.216.x.x
TTL:   3600
```

DNS changes take between 5 minutes and 48 hours to propagate. Usually it's under
an hour. You can verify with: `dig your-domain.com` or `nslookup your-domain.com`.

---

## Part 3 — Code and Version Control

### 3.1 The golden rule of version control

**Every piece of code lives in Git. Nothing important lives only on the server.**

The server is ephemeral — it can fail, be deleted, or need to be rebuilt. Your
GitHub repository is the canonical source of truth. The server is just a place
where the code runs.

### 3.2 GitHub repository structure

Your repo should have this structure:

```
ics/                        ← project root
  backend/                  ← Django project (ics_project/, accounts/, etc.)
    manage.py
    requirements.txt
    gunicorn.conf.py
    .env.example            ← template for .env (no real secrets)
    ics_project/
      settings/
        base.py
        local.py
        production.py
  frontend/                 ← static assets (CSS, JS, images)
    assets/
      css/
      js/
  deploy.sh                 ← deployment script (see Part 8)
  README.md
  .gitignore
```

### 3.3 What must NEVER go into Git

Create a `.gitignore` file in your project root:

```
# .gitignore

# Environment secrets — CRITICAL: never commit this
.env
*.env
.env.local
.env.production

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
*.egg-info/

# Django
staticfiles/
media/
db.sqlite3

# Editors
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

The most important line is `.env`. Your `.env` file contains your database password,
secret key, and other secrets. If you accidentally commit it to a public GitHub repo,
you must immediately rotate all those secrets. Prevent this with the `.gitignore`.

### 3.4 `.env.example` — the safe version

Create a file called `.env.example` (this one IS committed to Git):

```
# .env.example — copy this to .env and fill in real values
# Never commit the actual .env file

SECRET_KEY=replace-with-a-long-random-string
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_NAME=ics_db
DB_USER=ics_user
DB_PASSWORD=replace-with-your-db-password
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

This tells anyone setting up the project what environment variables they need,
without exposing the actual values.

### 3.5 The deploy key — giving the server read access to GitHub

The server needs to pull code from GitHub. You do this with a deploy key (a
read-only SSH key on the server):

```bash
# On the SERVER (as ics user):
ssh-keygen -t ed25519 -C "ics-production-deploy"
# Save to: /home/ics/.ssh/id_ed25519_deploy
# No passphrase (so automated scripts can use it)

# View the public key
cat /home/ics/.ssh/id_ed25519_deploy.pub

# In GitHub: Settings → Deploy keys → Add deploy key
# Paste the public key. Title: "ics-production". Read only: YES.
# Save.

# Tell SSH to use this key for GitHub
nano /home/ics/.ssh/config
```

Add this to `/home/ics/.ssh/config`:

```
Host github.com
  HostName github.com
  User git
  IdentityFile /home/ics/.ssh/id_ed25519_deploy
```

```bash
# Test it
ssh -T git@github.com
# Expected: Hi username! You've successfully authenticated...
```

Now you can clone your repo:

```bash
cd ~
git clone git@github.com:your-username/ics.git
```

---

## Part 4 — The Development Loop

### 4.1 The two environments

You always have two environments running in parallel:

| Environment | Where | Purpose | URL |
|-------------|-------|---------|-----|
| **Local** | Your laptop | Active development, writing code, testing changes | `http://localhost:8000` |
| **Production** | Hetzner VPS | Real users, real data | `https://your-domain.com` |

You develop locally. You deploy to production when the code is ready.

### 4.2 Local development setup

On your laptop:

```bash
# Clone the repo (first time only)
git clone git@github.com:your-username/ics.git
cd ics/backend

# Create a virtual environment
python3.11 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the env template and fill in LOCAL values
cp .env.example .env
nano .env
# Set DEBUG=True, use your local PostgreSQL credentials

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
# Visit http://localhost:8000
```

### 4.3 The daily development cycle

```
Write code → Test locally → Commit to Git → Push to GitHub → Deploy to production
```

In practice, a working day looks like this:

```bash
# Start of day: pull latest changes
git pull origin main

# Work on a feature
# Edit files in VS Code...

# Test your changes locally
python manage.py runserver
# Check http://localhost:8000

# When satisfied, commit
git add .
git commit -m "feat: learn app progress bar HTMX partial"

# Push to GitHub
git push origin main

# Deploy to production (see Part 8)
./deploy.sh
```

### 4.4 Commit message conventions

Good commit messages make the history readable. The ICS project already uses this
pattern — stick to it:

```
feat:  a new feature (feat: bible app annotations)
fix:   a bug fix (fix: certification queue not showing draft records)
chore: maintenance, config, tooling (chore: update requirements.txt)
docs:  documentation only (docs: update README with deploy steps)
refactor: code reorganisation with no behaviour change
```

**One commit per logical unit of work.** One app per commit is the ICS convention.
Don't bundle five things into one commit — you can't undo half of it later.

---

## Part 5 — Secrets and Environment Variables

### 5.1 What a secret is

A secret is any value that would cause harm if made public:
- Database password
- Django `SECRET_KEY`
- Email service API keys
- Any third-party API credentials

### 5.2 How secrets are managed in this project

The ICS project uses `python-decouple` to read secrets from a `.env` file. The
`.env` file lives on the server at `/home/ics/ics/backend/.env` and is never
committed to Git.

```bash
# On the server — creating the .env file
nano /home/ics/ics/backend/.env
```

Fill it with real values:

```
SECRET_KEY=generate-a-50-character-random-string-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_NAME=ics_db
DB_USER=ics_user
DB_PASSWORD=your-actual-strong-db-password
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://your-domain.com
DJANGO_SETTINGS_MODULE=ics_project.settings.production
```

```bash
# Lock down the .env file — only the ics user can read it
chmod 600 /home/ics/ics/backend/.env
```

### 5.3 Generating a SECRET_KEY

Django's `SECRET_KEY` must be long, random, and unique to your deployment:

```bash
# On the server or your laptop:
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
# Copy the output and paste it as SECRET_KEY in your .env
```

**Never reuse a SECRET_KEY between projects. Never share it.**

### 5.4 Rotating secrets

If a secret is compromised (e.g. you accidentally committed `.env`):

1. Change the secret at the source (new DB password, new Django secret key, etc.)
2. Update `/home/ics/ics/backend/.env` on the server
3. Restart Gunicorn: `sudo systemctl restart ics`
4. Rotate any API keys at their respective services

---

## Part 6 — Backups

### 6.1 What needs to be backed up

| What | Why | How often |
|------|-----|-----------|
| PostgreSQL database | All user data, records, activities | Daily |
| `.env` file | Secrets and config | When it changes |
| Nginx config | Server routing config | When it changes |
| Code | Already in GitHub — no separate backup needed | n/a |

**The code is in GitHub. That is its backup. The database is not — you must back it up.**

### 6.2 Database backup script

Create `/home/ics/backup.sh`:

```bash
#!/bin/bash

# ICS Database Backup Script
# Run daily via cron

set -e  # Exit on any error

# Configuration
DB_NAME="ics_db"
DB_USER="ics_user"
BACKUP_DIR="/home/ics/backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/ics_db_$DATE.sql.gz"
RETENTION_DAYS=14  # Keep 14 days of backups

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create the backup
echo "[$DATE] Starting database backup..."
pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$BACKUP_FILE"
echo "[$DATE] Backup created: $BACKUP_FILE"

# Delete backups older than retention period
find "$BACKUP_DIR" -name "ics_db_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
echo "[$DATE] Old backups cleaned up (keeping $RETENTION_DAYS days)"

echo "[$DATE] Backup complete."
```

```bash
# Make it executable
chmod +x /home/ics/backup.sh

# Test it manually
/home/ics/backup.sh

# Schedule it to run every day at 2am via cron
crontab -e
# Add this line:
0 2 * * * /home/ics/backup.sh >> /var/log/ics/backup.log 2>&1
```

### 6.3 Restoring from backup

If you ever need to restore the database:

```bash
# Stop the application first
sudo systemctl stop ics

# Restore from a backup file
gunzip -c /home/ics/backups/ics_db_2026-04-12_02-00-00.sql.gz | \
  psql -U ics_user -h localhost ics_db

# Start the application again
sudo systemctl start ics
```

### 6.4 Off-server backups (important)

Backups stored on the same server as the data are not true backups — if the server
is deleted or corrupted, you lose both. For a first production project, the simplest
off-server solution is to copy backups to a second location.

The easiest free option: copy daily backups to a separate cloud storage. For now,
even manually downloading backups to your laptop weekly is better than nothing.
Hetzner also offers their own storage volumes and object storage that can be added
to your server at low cost.

---

## Part 7 — Monitoring

### 7.1 What monitoring means

Monitoring means knowing when something is wrong before a user tells you. At the
most basic level for ICS MVP, this means:

- Knowing when the server goes down
- Knowing when Django throws an error
- Knowing when disk space is running out

### 7.2 Uptime monitoring (free)

Sign up for [UptimeRobot](https://uptimerobot.com) (free tier). Add a monitor for
your health check endpoint:

```
URL:  https://your-domain.com/api/health/
Type: HTTP(s)
Interval: Every 5 minutes
Alert: Email when down
```

UptimeRobot will ping your server every 5 minutes and email you if it stops
responding. This is the minimum monitoring for a production app.

### 7.3 Server resource monitoring

Check these regularly (at least weekly):

```bash
# Disk space — if this fills up, the server stops working
df -h
# Look for: Filesystem on / — if "Use%" is above 80%, you need to take action

# Memory usage
free -h
# Look for: "available" column — should be at least a few hundred MB

# Running processes
ps aux | grep gunicorn
# Should show 3-4 gunicorn worker processes

# Nginx status
sudo systemctl status nginx

# Gunicorn/ICS status
sudo systemctl status ics
```

### 7.4 Application error logs

Django errors are written to `/var/log/ics/django_errors.log`. Check this file
when something isn't working:

```bash
# View the last 50 lines of the error log
tail -50 /var/log/ics/django_errors.log

# Watch the log in real time (useful during a deploy)
tail -f /var/log/ics/django_errors.log

# Gunicorn access log (all HTTP requests)
tail -50 /var/log/gunicorn/ics_access.log

# Nginx logs
sudo tail -50 /var/log/nginx/error.log
```

### 7.5 Setting up email alerts from Django

Add to `production.py` to have Django email you on 500 errors:

```python
ADMINS = [('Your Name', 'your-email@example.com')]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'          # or your email provider's SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
SERVER_EMAIL = config('EMAIL_HOST_USER')
```

Add `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` to your `.env` file. Django will
then automatically email you (the `ADMINS`) whenever a 500 error occurs.

---

## Part 8 — Deploying Changes

### 8.1 What a deployment is

A deployment is the act of copying new code from GitHub to the server and
restarting the application. The goal is to do this with zero downtime and in a
repeatable, safe way.

### 8.2 The deploy script

Create `deploy.sh` in your project root (committed to Git):

```bash
#!/bin/bash

# ICS Platform — Deploy Script
# Run from your LOCAL machine: ./deploy.sh
# Requires: ssh access to the server as ics user

set -e  # Stop on any error

SERVER="ics@your-domain.com"
APP_DIR="/home/ics/ics/backend"

echo "=== ICS Deploy starting ==="

# Run deployment commands on the server
ssh "$SERVER" << 'ENDSSH'
  set -e
  cd /home/ics/ics/backend

  echo "[1/6] Pulling latest code from GitHub..."
  git pull origin main

  echo "[2/6] Activating virtual environment..."
  source /home/ics/ics/venv/bin/activate

  echo "[3/6] Installing/updating dependencies..."
  pip install -r requirements.txt --quiet

  echo "[4/6] Running database migrations..."
  export DJANGO_SETTINGS_MODULE=ics_project.settings.production
  python manage.py migrate --no-input

  echo "[5/6] Collecting static files..."
  python manage.py collectstatic --no-input --quiet

  echo "[6/6] Restarting Gunicorn..."
  sudo systemctl restart ics

  echo "=== Deploy complete ==="
ENDSSH

echo "=== Verifying health check ==="
sleep 3
curl -sf https://your-domain.com/api/health/ && echo "✓ Health check passed" || echo "✗ Health check FAILED"
```

```bash
# Make it executable
chmod +x deploy.sh

# Run a deployment
./deploy.sh
```

### 8.3 Before every deployment — the checklist

Before running `deploy.sh`, confirm:

- [ ] All changes are committed: `git status` shows clean
- [ ] All changes are pushed: `git push origin main`
- [ ] You have tested the change locally
- [ ] If you changed models: migration files exist (`python manage.py makemigrations`)
- [ ] If you changed requirements: `requirements.txt` is updated

### 8.4 When a deployment goes wrong

If the deployment fails or the site breaks after a deployment:

```bash
# On the server — rollback to the previous commit
cd /home/ics/ics/backend
git log --oneline -5    # find the commit hash before the broken one
git checkout <commit-hash>  # roll back the code
sudo systemctl restart ics

# Then investigate what went wrong before pushing again
```

---

## Part 9 — Standard Documentation

### 9.1 Why documentation matters

Production projects have documentation for a simple reason: you will forget how
things work. Six months from now, you will not remember why you made a particular
decision, what command initialises the database, or how to add a new admin user.
Good documentation saves you from yourself.

It also enables someone else (a developer, a volunteer, a future team member) to
work on the project without needing you to explain everything.

### 9.2 The documents every production project must have

These files live in the root of your repository:

| File | Purpose |
|------|---------|
| `README.md` | Project overview, setup instructions, how to run locally |
| `DEPLOY.md` | How to deploy to production, step by step |
| `ARCHITECTURE.md` | High-level system design — what each component does and why |
| `CHANGELOG.md` | A record of what changed in each version |
| `.env.example` | Template for environment variables (no real secrets) |
| `requirements.txt` | Python dependencies with pinned versions |

### 9.3 README.md — what it must contain

```markdown
# ICS Platform — Integrated Community System

Brief description of what the platform is (2-3 sentences).

## Quick Start (Local Development)

1. Clone the repo: `git clone ...`
2. Create virtual environment: `python3.11 -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy .env: `cp .env.example .env` and fill in values
6. Run migrations: `python manage.py migrate`
7. Start server: `python manage.py runserver`
8. Visit: http://localhost:8000

## Project Structure

Brief description of what's in each directory.

## Tech Stack

Django 4.2 LTS, PostgreSQL, Nginx, Gunicorn, HTMX.

## References

- Data Contract: docs/data-contract-v9.md
- Build Roadmap: docs/build-roadmap-v3.md
- HTMX ADR: docs/htmx-migration-adr.md
```

### 9.4 CHANGELOG.md — what it must contain

```markdown
# Changelog

All notable changes to this project will be documented here.
Format: [Version] — YYYY-MM-DD

## [0.5.0] — 2026-04-12
### Added
- Learn App: course catalogue, enrolment, progress tracking
- Learn App: steward certification queue

## [0.4.0] — 2026-04-08
### Added
- Bible App: three-panel HTMX reader, annotation system

## [0.3.0] — 2026-04-07
### Changed
- Frontend architecture: vanilla JS IIFE → Django templates + HTMX
```

Keep this updated with every significant release. It is your audit trail.

### 9.5 Pinning Python dependencies

Your `requirements.txt` should pin exact versions to prevent surprises:

```
# Good — pinned versions (production-safe)
django==4.2.11
djangorestframework==3.15.1
psycopg2-binary==2.9.9
gunicorn==21.2.0
python-decouple==3.8

# Bad — unpinned (breaks unexpectedly when library updates)
django
djangorestframework
```

To generate a pinned requirements file from your current environment:

```bash
pip freeze > requirements.txt
```

Do this whenever you add or update a dependency.

---

## Part 10 — Maintenance

### 10.1 The ongoing work of running a server

Running a production server is not a one-time job. These are the recurring tasks:

| Task | Frequency | Time |
|------|-----------|------|
| Check UptimeRobot for alerts | Automated — just read emails | — |
| Check disk space (`df -h`) | Weekly | 1 minute |
| Check error logs | Weekly | 5 minutes |
| Download a backup to laptop | Weekly | 5 minutes |
| Update system packages | Monthly | 10 minutes |
| Update Python dependencies | Monthly | 30 minutes |
| Renew SSL certificate | Automatic via certbot | — |

### 10.2 Monthly system updates

```bash
# On the server
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y   # remove packages no longer needed

# Restart if the kernel was updated
sudo reboot
# Wait ~30 seconds, then SSH back in
ssh ics@your-domain.com
```

### 10.3 Python dependency updates

```bash
# On your LOCAL machine, in the virtual environment
pip list --outdated    # see what has updates
pip install --upgrade <package-name>   # update one at a time, test after each
pip freeze > requirements.txt   # save the updated list
git add requirements.txt
git commit -m "chore: update dependencies"
./deploy.sh    # deploy the updates
```

Never update all packages at once. Update one at a time and test.

### 10.4 SSL certificate renewal

Let's Encrypt certificates expire after 90 days. `certbot` handles renewal
automatically via a timer. Verify the auto-renewal is working:

```bash
sudo certbot renew --dry-run
# Expected: "Congratulations, all renewals succeeded."
```

If this fails, your site will stop being accessible over HTTPS. Check it monthly.

### 10.5 Adding a superuser (Django admin)

When you need a new admin user for the Django `/admin/` panel:

```bash
# On the server
cd /home/ics/ics/backend
source /home/ics/ics/venv/bin/activate
export DJANGO_SETTINGS_MODULE=ics_project.settings.production
python manage.py createsuperuser
# Enter email, display name, and password
```

---

## Part 11 — DevOps Vocabulary Glossary

These are the terms used in this guide and in production engineering generally.
You will encounter all of them.

| Term | Plain-English meaning |
|------|-----------------------|
| **VPS** | Virtual Private Server — a computer in a data centre you rent by the month. Your Hetzner server is a VPS. |
| **SSH** | Secure Shell — the encrypted tunnel you use to type commands on the remote server from your laptop. |
| **SSH key** | A cryptographic pair of files (public + private) that authenticate you to a server without a password. |
| **Nginx** | The web server that sits in front of your Django app. It handles HTTPS, static files, and passes all other requests to Gunicorn. |
| **Gunicorn** | The Python application server that runs Django. Nginx talks to Gunicorn; Gunicorn runs your code. |
| **systemd** | The Linux process manager. It starts Gunicorn when the server boots and restarts it if it crashes. |
| **Git** | Version control — a system that tracks every change to every file in your codebase. |
| **GitHub** | A website that hosts your Git repository. Your code's remote backup. |
| **Deploy** | The act of taking new code from GitHub and making it run on the production server. |
| **Migration** | A file that describes a change to the database schema. Django applies migrations to keep the DB in sync with your models. |
| **Environment variable** | A value set outside of the code (in `.env`) that configures how the app runs. Secrets live here. |
| **.env file** | A file of environment variables. Never committed to Git. Lives only on the server and your laptop. |
| **SSL / TLS** | The encryption protocol that makes `https://` work. Let's Encrypt provides free SSL certificates. |
| **Firewall** | A set of rules that controls which network traffic is allowed in and out of the server. `ufw` is the tool that manages it. |
| **Cron** | A scheduler that runs commands at fixed intervals. Used to run the backup script at 2am every day. |
| **Virtualenv** | An isolated Python environment. Keeps ICS's dependencies separate from other Python projects. |
| **Static files** | CSS, JavaScript, and images. Django's `collectstatic` gathers them into one folder. Nginx serves them directly — faster than going through Gunicorn. |
| **Reverse proxy** | Nginx's role — it sits between the internet and Gunicorn, forwarding requests and handling SSL. |
| **Health check** | A simple endpoint (`/api/health/`) that returns `{"status": "ok"}`. Monitoring tools ping it to confirm the app is alive. |
| **Rollback** | Undoing a deployment by reverting to a previous version of the code. |
| **Zero downtime deploy** | A deployment method where the app stays available during the update. The ICS deploy script has brief downtime (~2 seconds) — acceptable for MVP. |

---

## Part 12 — Quick Reference Card

### Daily commands

```bash
# SSH into server
ssh ics@your-domain.com

# Check server status
sudo systemctl status ics
sudo systemctl status nginx

# View recent errors
tail -50 /var/log/ics/django_errors.log

# Deploy new code
./deploy.sh    # run from your laptop

# Restart the app (without deploying)
sudo systemctl restart ics
```

### Emergency commands

```bash
# App is down — restart it
sudo systemctl restart ics

# Nginx is down — restart it
sudo systemctl restart nginx

# Out of disk space — find large files
du -sh /var/log/* | sort -h

# Roll back to previous version
cd /home/ics/ics/backend
git log --oneline -5
git checkout <previous-commit-hash>
sudo systemctl restart ics
```

### Key file locations

```
/home/ics/ics/backend/          App code
/home/ics/ics/backend/.env      Secrets (never shared)
/home/ics/ics/venv/             Python virtual environment
/home/ics/ics/backend/staticfiles/  Collected static files
/home/ics/backups/              Database backups
/var/log/ics/                   Django error logs
/var/log/gunicorn/              Gunicorn access/error logs
/var/log/nginx/                 Nginx logs
/etc/nginx/sites-available/ics  Nginx site config
/etc/systemd/system/ics.service Gunicorn systemd config
```

---

## What to do next

You do not need to do all of this before you start building. Here is the order
that makes sense for the ICS project right now:

1. **Complete the Hetzner setup** (Parts 1–2) — provision the server, harden it, point the domain.
2. **Set up GitHub** (Part 3) — repo structure, `.gitignore`, `.env.example`, deploy key.
3. **Set up local development** (Part 4) — so you can work on your laptop.
4. **Continue the ICS build** (Task 5.2 Learn App) — the server and GitHub can wait until the app is closer to complete.
5. **Set up backups** (Part 6) — do this as soon as the database has real data.
6. **Set up UptimeRobot** (Part 7) — takes 5 minutes, gives you immediate peace of mind.
7. **Write README and CHANGELOG** (Part 9) — do this incrementally, not all at once.

You are further along than you think. The hard architectural decisions are locked.
The build is ordered. The documents exist. What you need now is the operational
layer around the build — and this guide covers that.
