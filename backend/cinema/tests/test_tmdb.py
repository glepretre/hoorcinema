import io
import json
from urllib.error import HTTPError, URLError

import pytest

from cinema.tmdb import TMDbClient, TMDbError


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_tmdb_client_sends_authentication_and_parameters(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response(json.dumps({"results": [{"id": 42}]}).encode())

    monkeypatch.setattr("cinema.tmdb.urlopen", fake_urlopen)

    payload = TMDbClient("test-token", timeout=3).get_popular_movies(
        page=2, language="fr-FR"
    )

    assert payload == {"results": [{"id": 42}]}
    assert captured["timeout"] == 3
    assert captured["request"].get_header("Authorization") == "Bearer test-token"
    assert captured["request"].full_url.endswith("page=2&language=fr-FR")


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (HTTPError("url", 429, "rate limited", {}, None), "HTTP 429"),
        (TimeoutError(), "timed out"),
        (URLError(TimeoutError()), "timed out"),
    ],
)
def test_tmdb_client_reports_network_errors(monkeypatch, error, message):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr("cinema.tmdb.urlopen", fail)

    with pytest.raises(TMDbError, match=message):
        TMDbClient("test-token").get_movie_details(42)


def test_tmdb_client_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr("cinema.tmdb.urlopen", lambda *args, **kwargs: Response(b"{"))

    with pytest.raises(TMDbError, match="invalid JSON"):
        TMDbClient("test-token").get_movie_credits(42)
