from django.urls import path

from cinema.views import health, hello

urlpatterns = [
    path("health/", health, name="health"),
    path("hello/", hello, name="hello"),
]
