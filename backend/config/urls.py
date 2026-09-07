from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("cinema.urls")),
]

if settings.FRONTEND_DIST_DIR.is_dir():
    frontend = TemplateView.as_view(template_name="index.html")
    urlpatterns += [
        path("", frontend, name="frontend"),
        path("login/", frontend, name="frontend-login"),
        path("films/", frontend, name="frontend-films"),
        path("films/archives/", frontend, name="frontend-archives"),
        path("films/<int:film_id>/", frontend, name="frontend-film"),
    ]
