from BTrees.OOBTree import OOBTree
from collective.listmonk import listmonk
from collective.listmonk.services.base import PydanticService
from datetime import datetime
from datetime import timezone
from plone import api
from urllib.parse import quote
from zExceptions import BadRequest

import pydantic
import uuid


class SubscriptionRequest(pydantic.BaseModel):
    list_ids: list[int]
    name: str
    email: str


class PendingConfirmation(pydantic.BaseModel):
    token: str
    list_ids: list[int]
    sub_id: int
    created_at: datetime = pydantic.Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class CreateSubscription(PydanticService):
    def reply(self):
        data = self.validate_body(SubscriptionRequest)

        subscriber = listmonk.get_subscriber(data.email)
        if subscriber:
            # Subscriber already exists. Add new (unconfirmed) subscription.
            listmonk.call_listmonk(
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
            result = listmonk.call_listmonk(
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

        pc = create_pending_confirmation(subscriber["id"], data)
        navroot = api.portal.get_navigation_root(self.context)
        confirm_link = (
            f"{navroot.absolute_url()}/subscriptions/confirm?token={quote(pc.token)}"
        )
        send_confirmation(data, confirm_link)


class ConfirmSubscriptionRequest(pydantic.BaseModel):
    token: str


class ConfirmSubscription(PydanticService):
    def reply(self):
        data = self.validate_body(ConfirmSubscriptionRequest)
        storage = get_pending_confirmation_storage()
        try:
            pc = PendingConfirmation.model_validate(storage[data.token])
        except KeyError:
            raise BadRequest("Invalid token.")
        listmonk.call_listmonk(
            "put",
            "/subscribers/lists",
            json={
                "ids": [pc.sub_id],
                "action": "add",
                "target_list_ids": pc.list_ids,
                "status": "confirmed",
            },
        )
        del storage[data.token]


class UnsubscribeRequest(pydantic.BaseModel):
    list_ids: list[int]
    email: str


class Unsubscribe(PydanticService):
    def reply(self):
        data = self.validate_body(UnsubscribeRequest)
        subscriber = listmonk.get_subscriber(data.email)
        if subscriber is None:
            raise BadRequest("Subscription not found")
        listmonk.call_listmonk(
            "put",
            "/subscribers/lists",
            json={
                "ids": [subscriber["id"]],
                "action": "unsubscribe",
                "target_list_ids": data.list_ids,
            },
        )


def get_pending_confirmation_storage() -> OOBTree:
    """Get or create the BTree used to track pending confirmations."""
    portal = api.portal.get()
    if not hasattr(portal, "_listmonk_pending_confirmations"):
        portal._listmonk_pending_confirmations = OOBTree()
    return portal._listmonk_pending_confirmations


def create_pending_confirmation(
    sub_id: int, data: SubscriptionRequest
) -> PendingConfirmation:
    storage = get_pending_confirmation_storage()
    token = uuid.uuid4().hex
    pc = PendingConfirmation(token=token, sub_id=sub_id, list_ids=data.list_ids)
    storage[token] = pc.model_dump()
    return pc


def send_confirmation(data: SubscriptionRequest, confirm_link: str):
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
    api.portal.send_email(
        recipient=data.email,
        subject=subject,
        body=body,
        immediate=True,
    )
