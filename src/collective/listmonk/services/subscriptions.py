from BTrees.OOBTree import OOBTree
from collective.listmonk import _
from collective.listmonk import listmonk
from collective.listmonk.content.newsletter import Newsletter
from collective.listmonk.services.base import PydanticService
from datetime import datetime
from datetime import timezone
from plone import api
from urllib.parse import quote
from zExceptions import BadRequest
from zope.i18n import translate

import pydantic
import transaction
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
    context: Newsletter

    def reply(self):
        data = self.validate_body(SubscriptionRequest)

        available_list_ids = [int(topic["list_id"]) for topic in self.context.topics]
        list_ids = [
            list_id for list_id in data.list_ids if list_id in available_list_ids
        ]
        if not list_ids:
            raise Exception(
                translate(
                    _(
                        "error_no_lists",
                        default="Please select a topic to subscribe to.",
                    ),
                    context=self.request,
                )
            )

        subscriber = listmonk.find_subscriber(email=data.email)
        if subscriber:
            # Subscriber already exists. Add new (unconfirmed) subscription.
            listmonk.call_listmonk(
                "put",
                "/subscribers/lists",
                json={
                    "ids": [subscriber["id"]],
                    "action": "add",
                    "target_list_ids": list_ids,
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
                    "lists": list_ids,
                },
            )
            subscriber = result["data"]

        pc = create_pending_confirmation(subscriber["id"], data)
        transaction.commit()
        self.send_confirmation(data, pc)

    def send_confirmation(self, data: SubscriptionRequest, pc: PendingConfirmation):
        confirm_path = translate(
            _("path_confirm", default="newsletter-confirm"), context=self.request
        )
        confirm_link = (
            f"{self.context.absolute_url()}/{confirm_path}?token={quote(pc.token)}"
        )
        subject = translate(
            self.context.confirm_email_subject, context=self.request
        ).format(newsletter=self.context.title)
        body = translate(self.context.confirm_email_body, context=self.request).format(
            newsletter=self.context.title, confirm_link=confirm_link
        )
        api.portal.send_email(
            sender=self.context.get_email_sender(),
            recipient=data.email,
            subject=subject,
            body=body,
            immediate=True,
        )


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
        transaction.commit()
        self.send_confirmation(pc)

    def send_confirmation(self, pc: PendingConfirmation):
        subscriber = listmonk.call_listmonk("get", f"/subscribers/{pc.sub_id}")
        email = subscriber["data"]["email"]
        subject = translate(
            _("email_subscribed_subject", default="Subscription confirmed"),
            context=self.request,
        )
        unsubscribe_link = (
            f"{self.context.get_unsubscribe_link()}?s={subscriber['data']['uuid']}"
        )
        body = (
            translate(
                _(
                    "email_subscribed_body",
                    default="You are now subscribed to the ${newsletter}",
                    mapping={
                        "newsletter": self.context.title,
                    },
                ),
                context=self.request,
            )
            + "\n\n"
            + translate(
                _(
                    "email_mailing_footer",
                    default="---\nTo unsubscribe, please click on the following link:\n${unsubscribe_link}",
                    mapping={"unsubscribe_link": unsubscribe_link},
                ),
                context=self.request,
            )
        )
        api.portal.send_email(
            sender=self.context.get_email_sender(),
            recipient=email,
            subject=subject,
            body=body,
            immediate=True,
        )


class UnsubscribeRequest(pydantic.BaseModel):
    list_ids: list[int] = None
    sub_uuid: str


class Unsubscribe(PydanticService):
    def reply(self):
        data = self.validate_body(UnsubscribeRequest)
        list_ids = data.list_ids
        if list_ids is None:
            list_ids = [int(topic["list_id"]) for topic in self.context.topics]

        subscriber = listmonk.find_subscriber(uuid=data.sub_uuid)
        if subscriber is None:
            raise BadRequest("Subscription not found")
        current_lists = [
            list["id"]
            for list in subscriber["lists"]
            if list["subscription_status"] == "confirmed"
        ]
        if set(current_lists) - set(list_ids):
            # Some subscriptions will remain.
            # Unsubscribe from the others.
            listmonk.call_listmonk(
                "put",
                "/subscribers/lists",
                json={
                    "ids": [subscriber["id"]],
                    "action": "unsubscribe",
                    "target_list_ids": list_ids,
                },
            )
        else:
            # Unsubscribing from all lists.
            # Delete the subscriber.
            listmonk.call_listmonk(
                "delete",
                f"/subscribers/{subscriber['id']}",
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
