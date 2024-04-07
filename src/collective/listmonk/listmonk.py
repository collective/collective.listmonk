from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from typing import Optional
from zExceptions import BadRequest

import requests
import time


class ListmonkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="listmonk_")

    url: str = "http://localhost:9000/api"
    username: str = "admin"
    password: str = "admin"


settings = ListmonkSettings()


def call_listmonk(method, path, **kw):
    func = getattr(requests, method.lower())
    url = settings.url.rstrip("/") + "/" + path.lstrip("/")
    try:
        response = func(url, auth=(settings.username, settings.password), **kw)
    except ConnectionError:
        time.sleep(2)
        response = func(url, auth=(settings.username, settings.password), **kw)
    try:
        response.raise_for_status()
    except HTTPError as err:
        if err.response.status_code == 400:
            raise err.__class__(err.response.json()["message"])
        raise
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
