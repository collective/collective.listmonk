from plone.restapi.testing import RelativeSession
from typing import Optional
from zExceptions import BadRequest


# TODO get real values from configuration
listmonk = RelativeSession("http://localhost:9000/api")
listmonk.auth = ("admin", "admin")


def call_listmonk(method, path, **kw):
    func = getattr(listmonk, method.lower())
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
