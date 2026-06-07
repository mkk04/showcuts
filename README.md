# Showcuts

A Django web app that renders Apple **Shortcuts** (shared via iCloud links) as
readable, browsable action lists.

- Modern stack: **Django 5.2 LTS**, Django REST Framework, WhiteNoise.
- Recognises newer/unknown Shortcut actions automatically (see
  `share/process/lookups/infer.py`).
- Configuration is entirely environment-driven — no `local_settings.py` needed.

---

## Local development

Requirements: **Python 3.12** (3.10–3.13 supported).

```bash
# 1. Install dependencies (a virtualenv is recommended)
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env          # then edit if you like

# 3. Build assets + database
python manage.py compile_scss        # SCSS -> CSS
python manage.py migrate
python manage.py createsuperuser     # optional, for /admin and login

# 4. Run
python manage.py runserver
```

The site is now at <http://127.0.0.1:8000/>.

### Useful commands

| Command | Purpose |
| --- | --- |
| `python manage.py compile_scss` | Recompile `staticfiles/css/*.scss` to `.css` |
| `python manage.py test share.tests.test_views share.tests.test_models` | Run the offline test suite |
| `python manage.py collectstatic` | Gather static files into `static_collected/` |

> The action "battery" tests under `share/tests/test_batteries/` fetch live
> Shortcuts from iCloud and therefore require network access.

---

## Deploy to Render (free)

This repo ships a [Render Blueprint](https://render.com/docs/blueprint-spec)
(`render.yaml`), so deployment is essentially one click.

1. Push this repository to GitHub.
2. In the Render dashboard choose **New → Blueprint** and select the repo.
3. Render reads `render.yaml`, runs `build.sh`, and starts the app with
   `gunicorn`. A secret key is generated automatically and the public hostname
   is trusted automatically.

When the build finishes, create your admin/login account from the Render
**Shell** tab:

```bash
python manage.py createsuperuser
```

### Configuration (environment variables)

| Variable | Default | Notes |
| --- | --- | --- |
| `DJANGO_DEBUG` | `True` | Set to `False` in production (the Blueprint does this). |
| `DJANGO_SECRET_KEY` | dev fallback | Generated automatically on Render. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Render's hostname is added automatically. |
| `DATABASE_URL` | SQLite file | Set to a Postgres URL for persistent storage. |
| `DJANGO_TIME_ZONE` | `UTC` | |

### A note on the database

The free plan's disk is **ephemeral**, so the default SQLite database is reset
on every deploy/restart. That is fine for a demo. For persistent data, create a
free Postgres database (Render's own, or [Neon](https://neon.tech)) and set its
connection string as `DATABASE_URL` — no code changes required. The optional
Postgres wiring is included (commented out) in `render.yaml`.

---

## Working with actions

Apple keeps adding actions. There are three ways to deal with ones this app
doesn't recognise yet:

### 1. Inspect & export a Shortcut
On any Shortcut page, the **ⓘ Inspect** button (`/share/view/<id>/inspect`)
lists every action with its recognised/unrecognised state. From there you can:
- **Export Markdown** (`/share/view/<id>/export.md`) — a clean text version of
  the Shortcut, ideal for handing to an AI assistant to work on together.
- **Rebuild from iCloud** — re-fetch and re-render (applies newly added actions).

### 2. Add an action at runtime (no deploy)
The **action generator** (`/share/actions/`, login required) lets you define a
missing action from a simple form — identifier, name, category, glyph and a
title built line by line:

```
text: Do something with
magic: WFInput | Input        # variable field:  key | placeholder
inline: WFText | Text         # text-with-variables field
```

Saved definitions live in the database and apply immediately to newly
submitted Shortcuts (use **Rebuild** to apply them to existing ones). Unknown
actions on the Inspect page link straight to this form, pre-filled.

### 3. Hand-code an action (permanent)
For full control, add a class under
`share/process/sc_action/categories/` and register it in
`share/process/sc_action/directory.py`. The CLI command
`python manage.py inspect_shortcut <iCloud-link> --params` prints the exact
identifiers and parameters to build from.
