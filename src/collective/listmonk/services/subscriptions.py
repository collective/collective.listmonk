from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from plone.restapi.testing import RelativeSession
from typing import Optional
from zExceptions import BadRequest


class SubscriptionsPost(Service):
    def reply(self):
        data = json_body(self.request)
        email = data.get("email")
        if not email:
            raise BadRequest("Missing email")

        newsletter = self.context
        subscriber = get_subscriber(email)
        if subscriber:
            # Subscriber already exists. Add new (unconfirmed) subscription.
            # TODO handle case where subscription already exists
            call_listmonk(
                "put",
                "/subscribers/lists",
                json={
                    "ids": [subscriber["id"]],
                    "action": "add",
                    "target_list_ids": [newsletter.listmonk_id],
                    "status": "unconfirmed",
                },
            )
        else:
            # Add new subscriber and (unconfirmed) subscription.
            call_listmonk(
                "post",
                "/subscribers",
                json={
                    "email": email,
                    "name": "Unknown",  # TODO
                    "status": "enabled",
                    "lists": [newsletter.listmonk_id],
                },
            )


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
