# Deploy On Render

The root `Dockerfile` is the production image. It builds React, serves the
result and the Django administration static files through WhiteNoise, applies
database migrations, and starts Django with Gunicorn on Render's `$PORT`. The
development Dockerfiles under `backend/` and `frontend/` remain dedicated to
local Compose usage.

The simplest deployment uses the root `render.yaml` Blueprint, which creates a
single web service and its PostgreSQL database:

1. Push the repository to GitHub.
2. In Render, choose **New > Blueprint** and select the repository.
3. Review the two free resources and apply the Blueprint. `DJANGO_SECRET_KEY`
   is generated and `DATABASE_URL` is connected automatically. Leave
   `TMDB_API_TOKEN` empty if catalogue import is not needed.
4. In the OVH DNS zone, add the CNAME requested by Render for
   `hoorcinema.glepretre.fr`. Use Render's displayed target rather than an IP
   address.

The application, `/api/`, and `/admin/` all use the same domain, so no API
subdomain or CORS configuration is required. Django automatically accepts the
service's `onrender.com` hostname in addition to `DJANGO_ALLOWED_HOSTS`.

To adapt an already-created Render Web Service instead of using the Blueprint,
clear its **Root Directory**, select the Docker runtime, and set both the
Dockerfile path and build context to the repository root (`./Dockerfile` and
`.`). Add a Render PostgreSQL database, expose its internal connection string
as `DATABASE_URL`, and configure:

```text
DJANGO_SECRET_KEY=<a long random value>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=hoorcinema.glepretre.fr
```

After the first deployment, create an administrator from the Render Shell:

```bash
python manage.py createsuperuser
```

Render Shell access depends on the selected web-service plan. On a free service,
temporarily use a plan that provides Shell access if an administrator account is
required.
