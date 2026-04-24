# 🚀 KuliManje - Production Deployment Checklist

This document outlines the critical steps required to move the KuliManje platform from a development environment to a live production server (e.g., DigitalOcean, AWS, Linode).

## 1. Server Environment Setup
- [ ] **Python 3.12**: Ensure the latest stable version of Python is installed.
- [ ] **Redis Server**: Required for Django Channels and Notifications.
- [ ] **Gunicorn/Uvicorn**: Use Gunicorn for WSGI and Uvicorn for ASGI (WebSockets).
- [ ] **Nginx**: Set up as a reverse proxy for request handling and SSL termination.

## 2. Django Security & Configuration
- [ ] **SECRET_KEY**: Generate a unique key and store it in `.env`.
- [ ] **DEBUG**: Set to `False`. Never run production with `DEBUG=True`.
- [ ] **ALLOWED_HOSTS**: Add your domains (`example.com`, `www.example.com`).
- [ ] **CSRF_TRUSTED_ORIGINS**: Add your https domain to prevent CSRF errors on forms.
- [ ] **Security Middleware**: Ensure `SECURE_SSL_REDIRECT` is True in production settings.

## 3. Database & Static Assets
- [ ] **Migrate to PostgreSQL**: Strongly recommended over SQLite for production-grade concurrency.
- [ ] **Run Migrations**: `python manage.py migrate`
- [ ] **Collect Static Files**: `python manage.py collectstatic`. Ensure Nginx points to the static root.
- [ ] **Media Permissions**: Ensure the web server has write access to the `media/` directory for article images.

## 4. Real-time & Asynchronous Workers
- [ ] **Daphne/Uvicorn**: Run an ASGI server to handle real-time notifications via WebSockets.
- [ ] **Systemd**: Create service files for Gunicorn and Daphne to ensure they restart on system failure.

## 5. Final Pre-flight Checks
- [ ] **Check Logs**: Ensure the `logs/` directory exists and is writable.
- [ ] **Test Analytics**: Visit a public article and verify that a record is created in the `ArticleView` table.
- [ ] **Test Editor**: Open the "New Dispatch" portal and verify that TinyMCE loads correctly.
- [ ] **Email Testing**: Verify that forgotten password emails are sending via the configured SMTP server.

---
> [!IMPORTANT]
> Always perform a dry-run migration on a staging server before applying schema changes to a live production database.
