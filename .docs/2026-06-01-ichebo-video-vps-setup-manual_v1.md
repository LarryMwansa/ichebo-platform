# Ichebo Video VPS — Setup Manual

> **Document:** Video VPS Setup Manual  
> **Date:** 2026-06-01  
> **Server:** Hetzner VPS — `46.62.211.72` — Helsinki (hel1)  
> **OS:** Ubuntu 22.04 LTS  
> **Deploy user:** `ics`  
> **Version:** v1.0  

---

## Overview

This manual documents the complete setup of the Ichebo Video VPS — the server dedicated to Ichebo Media (Go Video Engine, MediaMTX RTMP ingest, HLS delivery). It is a CPU-reserved server that must never be loaded with Django or general application traffic. It is written as a step-by-step walkthrough so the process can be repeated, understood, and applied to new servers.

---

## Server Inventory

| Component | Detail |
|-----------|--------|
| Provider | Hetzner Cloud |
| Data centre | Helsinki — hel1 |
| IP | `46.62.211.72` |
| OS | Ubuntu 22.04 LTS |
| Deploy user | `ics` |
| Firewall | UFW — SSH, 80, 443 only |
| Web server | Nginx 1.18 |
| App services | None yet — Go Video Engine + MediaMTX (future) |

---

## Domains Configured

| Domain | Type | Target |
|--------|------|--------|
| `video.ichebo.org` | Placeholder | Go Video Engine (future) |
| `media.ichebo.org` | Placeholder | RTMP ingest / HLS delivery (future) |

Both domains currently return `503 Service Temporarily Unavailable` — intentional placeholder until the Go Video Engine is deployed.

---

## Part 1 — First Login as Root

When a Hetzner VPS is first provisioned, you log in as root via SSH.

```bash
ssh root@46.62.211.72
```

Run a quick inventory before doing anything:

```bash
# OS version
lsb_release -a

# What is already listening
ss -tlnp | grep LISTEN

# Firewall status
ufw status
```

Expected state on a fresh Hetzner VPS:
- Ubuntu 22.04 LTS
- Only SSH (port 22) listening
- UFW inactive

---

## Part 2 — System Updates

Always update all packages immediately after first login.

```bash
apt update && apt upgrade -y
```

---

## Part 3 — Create the Deploy User

Never run application services as root. Create a dedicated deploy user.

### 3.1 Create the user

```bash
adduser ics
```

Set a strong password when prompted. Press Enter to skip the name/phone fields.

### 3.2 Give sudo access

```bash
usermod -aG sudo ics
```

### 3.3 Copy SSH key from root

```bash
mkdir -p /home/ics/.ssh
cp /root/.ssh/authorized_keys /home/ics/.ssh/
chown -R ics:ics /home/ics/.ssh
chmod 700 /home/ics/.ssh
chmod 600 /home/ics/.ssh/authorized_keys
```

### 3.4 Test login before disabling root

**Open a second terminal** and test:

```bash
ssh ics@46.62.211.72
```

Confirm you can log in as `ics`. Do not proceed until this works.

---

## Part 4 — Harden SSH

Only after confirming `ics` login works, disable root SSH access.

```bash
sudo nano /etc/ssh/sshd_config
```

Find:
```
PermitRootLogin yes
```

Change to:
```
PermitRootLogin no
```

Save and restart SSH:

```bash
sudo systemctl restart sshd
```

From this point forward, all access is via the `ics` user only.

---

## Part 5 — Firewall (UFW)

Enable the firewall and allow only the required ports.

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Type `y` when prompted to confirm enabling.

Verify:

```bash
sudo ufw status
```

Expected output:
```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
OpenSSH (v6)               ALLOW       Anywhere (v6)
80/tcp (v6)                ALLOW       Anywhere (v6)
443/tcp (v6)               ALLOW       Anywhere (v6)
```

**Note:** When the Go Video Engine is deployed, additional ports will be opened for RTMP ingest (1935) at that time. Do not open them now.

---

## Part 6 — Install Nginx

Switch to the `ics` user for all remaining work:

```bash
su - ics
```

Install and enable Nginx:

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx | head -5
```

Expected: `Active: active (running)`

### 6.1 Remove the default site

The Nginx default site serves a generic page on port 80. Remove it:

```bash
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

---

## Part 7 — DNS Records

DNS must be configured and propagated before SSL can be provisioned.

### 7.1 Add A records for `ichebo.org`

In your domain registrar (Namecheap), add:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | `video` | `46.62.211.72` | 5 min |
| A Record | `media` | `46.62.211.72` | 5 min |

### 7.2 Verify propagation

```bash
dig +short video.ichebo.org @8.8.8.8
dig +short media.ichebo.org @8.8.8.8
```

Both must return `46.62.211.72` before proceeding.

---

## Part 8 — SSL Certificates

### 8.1 Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 8.2 Provision certs via standalone

```bash
sudo systemctl stop nginx

sudo certbot certonly --standalone -d video.ichebo.org
sudo certbot certonly --standalone -d media.ichebo.org

sudo systemctl start nginx
```

Certbot will ask for an email address on first run. Enter a valid address for renewal notices.

### 8.3 Create missing SSL config files

On a fresh server the `options-ssl-nginx.conf` file may not exist yet. Create it manually if needed:

```bash
# Check if it exists
ls /etc/letsencrypt/options-ssl-nginx.conf
```

If the file is missing (you will see "No such file or directory"), create it:

```bash
sudo bash -c 'cat > /etc/letsencrypt/options-ssl-nginx.conf << EOF
ssl_session_cache shared:le_nginx_SSL:10m;
ssl_session_timeout 1440m;
ssl_session_tickets off;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_ciphers "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384";
EOF'
```

Then generate the dhparam file (takes ~30 seconds):

```bash
sudo openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048
```

---

## Part 9 — Nginx Configuration

Create the Nginx config for both video domains:

```bash
sudo nano /etc/nginx/sites-available/ichebo-video
```

Paste this exactly:

```nginx
# ============================================================
# video.ichebo.org — Ichebo Media / Video Engine
# ============================================================
server {
    listen 80;
    server_name video.ichebo.org;
    return 301 https://video.ichebo.org$request_uri;
}

server {
    listen 443 ssl;
    server_name video.ichebo.org;

    ssl_certificate /etc/letsencrypt/live/video.ichebo.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/video.ichebo.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Placeholder — Go Video Engine will proxy here when built
    location / {
        return 503 "Ichebo Media — coming soon";
        add_header Content-Type text/plain;
    }
}

# ============================================================
# media.ichebo.org — RTMP ingest / HLS delivery endpoint
# ============================================================
server {
    listen 80;
    server_name media.ichebo.org;
    return 301 https://media.ichebo.org$request_uri;
}

server {
    listen 443 ssl;
    server_name media.ichebo.org;

    ssl_certificate /etc/letsencrypt/live/media.ichebo.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/media.ichebo.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Placeholder — MediaMTX/HLS delivery will proxy here when built
    location / {
        return 503 "Ichebo Media ingest — coming soon";
        add_header Content-Type text/plain;
    }
}
```

Enable and test:

```bash
sudo ln -s /etc/nginx/sites-available/ichebo-video /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Expected:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## Part 10 — Verification

```bash
curl -sI https://video.ichebo.org | head -5
# Expected: HTTP/1.1 503 Service Temporarily Unavailable

curl -sI https://media.ichebo.org | head -5
# Expected: HTTP/1.1 503 Service Temporarily Unavailable
```

503 is the correct response — it confirms Nginx is serving the domain with SSL, and the placeholder is active. The Go Video Engine will replace this when deployed.

---

## Part 11 — Adding a New Domain or Subdomain

This is the standard pattern for adding any new site to this server.

### Step 1 — DNS

Add A record in Namecheap:
- Host: subdomain name (e.g. `stream`)
- Value: `46.62.211.72`
- TTL: 5 min

Verify:
```bash
dig +short stream.ichebo.org @8.8.8.8
# Must return 46.62.211.72 before proceeding
```

### Step 2 — SSL

```bash
sudo systemctl stop nginx
sudo certbot certonly --standalone -d stream.ichebo.org
sudo systemctl start nginx
```

### Step 3 — Nginx config

Add a new server block to `/etc/nginx/sites-available/ichebo-video` or create a new file:

```bash
sudo nano /etc/nginx/sites-available/ichebo-stream
```

For a proxied service (Go binary on a local port):

```nginx
server {
    listen 80;
    server_name stream.ichebo.org;
    return 301 https://stream.ichebo.org$request_uri;
}

server {
    listen 443 ssl;
    server_name stream.ichebo.org;

    ssl_certificate /etc/letsencrypt/live/stream.ichebo.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/stream.ichebo.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Replace `PORT` with the port your Go service listens on.

### Step 4 — Enable and reload

```bash
sudo ln -s /etc/nginx/sites-available/ichebo-stream /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## Part 12 — What Comes Next (Future Sessions)

This server is prepared but not yet active. The following work happens in dedicated build sessions:

| Task                                                      | When                       |
| --------------------------------------------------------- | -------------------------- |
| Install Go + FFmpeg                                       | Ichebo Media build session |
| Deploy Go Video Engine                                    | Ichebo Media build session |
| Configure MediaMTX (RTMP)                                 | Ichebo Media build session |
| Open UFW port 1935 (RTMP)                                 | Ichebo Media build session |
| Update Nginx — replace 503 placeholders with proxy blocks | Ichebo Media build session |
| Configure Hetzner Object Storage buckets                  | Ichebo Media build session |

**Do not install Go, FFmpeg, or MediaMTX before the build session.** The server is intentionally kept clean until that point.

---

## Key File Locations

```
/home/ics/                                ← Deploy user home
/etc/nginx/sites-available/ichebo-video   ← Nginx config
/etc/nginx/sites-enabled/ichebo-video     ← Symlink to sites-available
/etc/letsencrypt/live/video.ichebo.org/   ← SSL cert — video
/etc/letsencrypt/live/media.ichebo.org/   ← SSL cert — media
/var/log/nginx/                           ← Nginx logs
```

---

## Quick Reference Commands

```bash
# SSH into server
ssh ics@46.62.211.72

# Test Nginx config
sudo nginx -t

# Reload Nginx (no downtime)
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# Check firewall
sudo ufw status

# Check what is listening
sudo ss -tlnp | grep LISTEN

# Check all SSL certs
sudo certbot certificates

# View Nginx errors
sudo tail -50 /var/log/nginx/error.log
```

---

## Architecture Note

This server is purpose-built for CPU-intensive video work. The constraint is hardware:

| What belongs here | What does not belong here |
|-------------------|--------------------------|
| Go Video Engine | Django apps |
| MediaMTX RTMP ingest | PostgreSQL |
| HLS segment serving | Celery workers |
| Static websites (low traffic) | Any background task competing with FFmpeg |

Live video transcoding consumes multiple CPU cores continuously. Never deploy anything with heavy background processing to this server.

---

*Ichebo Christian Services — Video VPS Setup Manual*  
*Compiled: 2026-06-01 — v1.0*
