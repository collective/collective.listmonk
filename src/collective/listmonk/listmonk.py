from plone.restapi.testing import RelativeSession
from typing import Optional
from zExceptions import BadRequest

import os


LISTMONK_API = os.environ.get("LISTMONK_API", "http://localhost:9000/api")
LISTMONK_USERNAME = os.environ.get("LISTMONK_USERNAME", "admin")
LISTMONK_PASSWORD = os.environ.get("LISTMONK_PASSWORD", "admin")

client = RelativeSession(LISTMONK_API)
client.auth = (LISTMONK_USERNAME, LISTMONK_PASSWORD)


def call_listmonk(method, path, **kw):
    func = getattr(client, method.lower())
    response = func(path, **kw)
    response.raise_for_status()
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
