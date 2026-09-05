from django.urls import reverse
from rest_framework.test import APIClient


def test_hello_returns_message():
    response = APIClient().get(reverse("hello"))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert response.json() == {"message": "Hello, World!"}
