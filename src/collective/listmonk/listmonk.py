from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from requests.exceptions import HTTPError
from typing import Optional
from urllib.parse import urljoin
from urllib.parse import urlparse
from zExceptions import BadRequest

import requests


class ListmonkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="listmonk_")

    url: str = "http://localhost:9000/api"
    username: str = "admin"
    password: str = "admin"


class RelativeSession(requests.Session):
    def __init__(self, base_url):
        super().__init__()

        if not base_url.endswith("/"):
            base_url += "/"
        self.__base_url = base_url

    def request(self, method, url, **kwargs):
        if urlparse(url).scheme not in ("http", "https"):
            url = url.lstrip("/")
            url = urljoin(self.__base_url, url)
        return super().request(method, url, **kwargs)


settings = ListmonkSettings()
client = RelativeSession(settings.url)
client.auth = (settings.username, settings.password)


def call_listmonk(method, path, **kw):
    func = getattr(client, method.lower())
    response = func(path, **kw)
    try:
        response.raise_for_status()
    except HTTPError as err:
        if err.response.status_code == 400:
            raise err.__class__(err.response.json()["message"])
    return response.json()


def get_subscriber(email: str) -> Optional[dict]:
    result = call_listmonk(
        "get",
        "/subscribers",
        params={"query": f"email='{email}'"},
    )
    count = result["data"]["total"]
    if count == 1:
        return result["data"]["results"][0]
    elif count > 1:
        raise BadRequest("Found more than one subscriber")
