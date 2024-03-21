from BTrees.OOBTree import OOBTree
from datetime import datetime
from datetime import timezone
from email.message import EmailMessage
from email.utils import formataddr
from plone import api
from plone.base.interfaces.controlpanel import IMailSchema
from plone.registry.interfaces import IRegistry
from plone.restapi.services import Service
from plone.restapi.testing import RelativeSession
from typing import Optional
from zExceptions import BadRequest
from zope.component import getUtility

import pydantic
import uuid


class SubscriptionRequest(pydantic.BaseModel):
    list_ids: list[int]
    name: str
    email: str


class ConfirmationToken(pydantic.BaseModel):
    token: str
    list_ids: list[int]
    sub_id: int
    created_at: datetime = pydantic.Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class SubscriptionsPost(Service):
    def reply(self):
        try:
            data = SubscriptionRequest.model_validate_json(self.request.get("BODY"))
        except pydantic.ValidationError as e:
            raise BadRequest(str(e))

        subscriber = get_subscriber(data.email)
        if subscriber:
            # Subscriber already exists. Add new (unconfirmed) subscription.
            call_listmonk(
                "put",
                "/subscribers/lists",
                json={
                    "ids": [subscriber["id"]],
                    "action": "add",
                    "target_list_ids": data.list_ids,
                    "status": "unconfirmed",
                },
            )
        else:
            # Add new subscriber and (unconfirmed) subscription.
            result = call_listmonk(
                "post",
                "/subscribers",
                json={
                    "email": data.email,
                    "name": data.name,
                    "status": "enabled",
                    "lists": data.list_ids,
                },
            )
            subscriber = result["data"]

        token = create_confirmation_token(subscriber["id"], data)
        navroot = api.portal.get_navigation_root(self.context)
        confirm_link = (
            f"{navroot.absolute_url()}/subscriptions/confirm?token={token.token}"
        )
        send_confirmation(data, confirm_link)


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


def get_confirmation_token_storage():
    """Get or create the BTree used to track confirmation tokens."""
    portal = api.portal.get()
    if not hasattr(portal, "_listmonk_confirmation_tokens"):
        portal._listmonk_confirmation_tokens = OOBTree()
    return portal._listmonk_confirmation_tokens


def create_confirmation_token(
    sub_id: int, data: SubscriptionRequest
) -> ConfirmationToken:
    storage = get_confirmation_token_storage()
    token = ConfirmationToken(
        token=uuid.uuid4().hex, sub_id=sub_id, list_ids=data.list_ids
    )
    storage[sub_id] = token.model_dump()
    return token


def send_confirmation(data: SubscriptionRequest, confirm_link: str):
    mailhost = api.portal.get_tool("MailHost")
    # lang = api.portal.get_current_language()
    # TODO show list titles instead of ids
    # TODO DE translation
    subject = "Confirm Subscription"
    body = f"""Confirm subscription

Someone has requested a subscription to the following newsletters: {data.list_ids}

To confirm this subscription, click this link:
{confirm_link}

If you did not request this subscription, you can ignore this email.
"""
    message = EmailMessage()
    message.set_content(body)
    mail_settings = get_mail_settings()
    from_name = mail_settings.email_from_name
    from_email = mail_settings.email_from_address
    mailhost.send(
        message.as_bytes(),
        data.email,
        formataddr((from_name, from_email)),
        subject=subject,
        charset="utf-8",
        immediate=True,
    )


def get_mail_settings():
    registry = getUtility(IRegistry)
    return registry.forInterface(IMailSchema, prefix="plone")
