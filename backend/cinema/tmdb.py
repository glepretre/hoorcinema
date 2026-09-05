import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TMDbError(Exception):
    """Raised when TMDb cannot provide a valid response."""


class TMDbClient:
    base_url = "https://api.themoviedb.org/3"

    def __init__(self, token, timeout=10):
        if not token:
            raise ValueError("A TMDb API token is required.")
        if timeout <= 0:
            raise ValueError("The TMDb timeout must be positive.")
        self.token = token
        self.timeout = timeout

    def get_popular_movies(self, *, page=1, language="en-US"):
        return self._get("/movie/popular", page=page, language=language)

    def get_movie_details(self, movie_id, *, language="en-US"):
        return self._get(f"/movie/{movie_id}", language=language)

    def get_movie_credits(self, movie_id, *, language="en-US"):
        return self._get(f"/movie/{movie_id}/credits", language=language)

    def _get(self, path, **params):
        url = f"{self.base_url}{path}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except HTTPError as error:
            raise TMDbError(f"TMDb returned HTTP {error.code} for {path}.") from error
        except TimeoutError as error:
            raise TMDbError(f"TMDb timed out while requesting {path}.") from error
        except URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise TMDbError(f"TMDb timed out while requesting {path}.") from error
            raise TMDbError(f"TMDb request failed for {path}.") from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TMDbError(f"TMDb returned invalid JSON for {path}.") from error

        if not isinstance(payload, dict):
            raise TMDbError(f"TMDb returned an invalid payload for {path}.")
        return payload
