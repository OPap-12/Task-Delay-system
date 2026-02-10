# Render Deployment Guide - Task Delay System

## ✅ Prerequisites
- A Render account
- This repository pushed to GitHub/GitLab
- (Optional) A managed database (Render PostgreSQL or external MySQL)

---

## 🚀 Quick Deploy (Render Blueprint)
This repo includes a `render.yaml` at the repository root. It sets `rootDir: task_delay_system` to run the Django app from the correct folder.
You can deploy with **Render Blueprint**:

1. Open Render → **New** → **Blueprint**
2. Select this repo
3. Render will auto-detect `render.yaml`
4. Click **Deploy**

---

## 🔐 Required Environment Variables

These are configured in `render.yaml` automatically. If deploying manually, add them in Render → **Environment**:

| Key | Example | Notes |
|-----|---------|-------|
| `DJANGO_SECRET_KEY` | auto-generated | Required for production |
| `DJANGO_DEBUG` | `False` | Must be false in prod |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com` | Comma-separated list |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` | Required for HTTPS |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` | Force HTTPS |
| `DJANGO_SESSION_COOKIE_SECURE` | `True` | Secure cookies |
| `DJANGO_CSRF_COOKIE_SECURE` | `True` | Secure cookies |
| `DJANGO_SECURE_HSTS_SECONDS` | `3600` | HSTS duration |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` | HSTS setting |
| `DJANGO_SECURE_HSTS_PRELOAD` | `True` | HSTS setting |

### Database
Render typically provides `DATABASE_URL` when you attach a managed database.

If using a database, set one of:
- `DATABASE_URL` (recommended)
- Or set `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

---

## 🗂️ Build + Start Commands

These are already in `render.yaml` and assume `requirements.txt` is at the repository root:

```bash
pip install -r ../requirements.txt
python manage.py collectstatic --noinput
gunicorn task_delay_system.wsgi:application
```

---

## ✅ Post-Deploy Steps

After deployment, open a Render shell and run:

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## ✅ Local Production Test

You can simulate production locally:

```bash
set DJANGO_DEBUG=False
set DJANGO_SECRET_KEY=replace-with-secure-key
set DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
python manage.py collectstatic --noinput
python manage.py runserver
```

---

## ✅ Notes
- Static files are served via **WhiteNoise**.
- HTTPS headers and cookie security are enabled by default.
- Debug errors are disabled in production.

---

## 🧰 Troubleshooting 500 Errors (Render)

If you see a **500 server error** on `/admin/login/` or `/login/`, follow these steps to capture the traceback:

1. In Render, open your service → **Logs**.
2. Click **"View All"** and look for a Python traceback right after the 500 request.
3. Copy the full traceback (it usually starts with `Traceback (most recent call last):`).

### Temporary DEBUG step (to surface the error)
If you still don’t see a traceback, temporarily set `DJANGO_DEBUG=True` in Render → Environment, redeploy, reproduce the error once, then turn it back **off**.

### Common causes to check
- **Migrations not applied**: run `python manage.py migrate`
- **Missing secret key**: ensure `DJANGO_SECRET_KEY` is set
- **Database not attached**: verify `DATABASE_URL` exists in Render env vars
- **Static file issues**: ensure `collectstatic` runs successfully
- **Superuser not created**: `python manage.py createsuperuser`

Once you have the traceback, share it and I can pinpoint the exact fix.
