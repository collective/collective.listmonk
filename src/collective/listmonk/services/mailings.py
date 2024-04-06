from annotated_types import Len
from collective.listmonk import listmonk
from collective.listmonk.content.newsletter import Newsletter
from collective.listmonk.services.base import deserialize_obj_link
from collective.listmonk.services.base import PydanticService
from datetime import datetime
from plone import api
from plone.app.uuid.utils import uuidToCatalogBrain
from plone.restapi.batching import HypermediaBatch
from plone.restapi.serializer.converters import json_compatible
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.query import And
from repoze.catalog.query import Eq
from repoze.catalog.query import NotEq
from souper.interfaces import ICatalogFactory
from souper.soup import get_soup
from souper.soup import NodeAttributeIndexer
from souper.soup import Record
from typing import Annotated
from typing import Optional
from zExceptions import BadRequest
from zope.interface import implementer
from ZTUtils.Lazy import LazyMap

import pydantic
import transaction


MAILINGS_SOUP = "collective.listmonk.mailings"


class MailingRequest(pydantic.BaseModel):
    subject: Annotated[str, Len(min_length=1)]
    body: str
    list_ids: list[int]
    based_on: Optional[str]
    send_test_to: Optional[list[str]] = None


class SendMailing(PydanticService):
    context: Newsletter

    def reply(self):
        data = self.validate_body(MailingRequest)

        if data.based_on:
            based_on = deserialize_obj_link(data.based_on)

        list_ids = []
        topics = []
        topics_by_list_id = {
            int(topic["list_id"]): topic for topic in self.context.topics
        }
        for list_id in data.list_ids:
            topic = topics_by_list_id.get(list_id)
            if topic:
                list_ids.append(list_id)
                topics.append(topic["title"])

        if not list_ids:
            raise BadRequest("Must specify at least one valid list.")

        is_test = data.send_test_to
        if not is_test:
            # Store mailing in Plone
            # (do this first so we only send the email once if there's a conflict error)
            record = Record()
            record.attrs.update(
                {
                    "subject": data.subject,
                    "newsletter": self.context.UID(),
                    "topics": topics,
                    "sent_at": datetime.now(),
                    "sent_by": api.user.get_current().getUserId(),
                    "based_on": based_on.UID() if based_on else None,
                }
            )
            portal = api.portal.get()
            get_soup(MAILINGS_SOUP, portal).add(record)
            transaction.commit()

        campaignData = {
            "name": data.subject,
            "subject": data.subject,
            "lists": list_ids,
            "type": "regular",
            "content_type": "plain",
            "body": self.context.get_email_body(data.body),
            "messenger": "email",
            "from_email": self.context.get_email_sender(),
        }

        # Create campaign in listmonk
        result = listmonk.call_listmonk(
            "post",
            "/campaigns",
            json=campaignData,
        )
        campaign = result["data"]
        if is_test:
            # Send test to specified subscribers
            listmonk.call_listmonk(
                "post",
                f"/campaigns/{campaign['id']}/test",
                json={
                    **campaignData,
                    "subscribers": data.send_test_to,
                },
            )
        else:
            # Start the draft campaign immediately
            listmonk.call_listmonk(
                "put",
                f"/campaigns/{campaign['id']}/status",
                json={
                    "status": "running",
                },
            )


class MailingsQuery(pydantic.BaseModel):
    based_on: Optional[str] = None
    newsletter: Optional[str] = None


class ListMailings(PydanticService):
    def reply(self):
        query = self.parse_query()
        results = self.run_query(query, sort_index="sent_at", reverse=True)
        return self.format_results(results)

    def parse_query(self):
        params = self.validate_params(MailingsQuery)
        criteria = []
        if params.based_on:
            criteria.append(Eq("based_on", deserialize_obj_link(params.based_on).UID()))
        if params.newsletter:
            criteria.append(
                Eq("newsletter", deserialize_obj_link(params.newsletter).UID())
            )
        if criteria:
            query = And(*criteria)
        else:
            query = NotEq("sent_at", datetime(2000, 1, 1))
        return query

    def run_query(self, queryobject, sort_index=None, reverse=False):
        portal = api.portal.get()
        soup = get_soup(MAILINGS_SOUP, portal)
        size, iids = soup.catalog.query(
            queryobject,
            sort_index=sort_index,
            reverse=reverse,
        )

        def get_record(i):
            return soup.data[i]

        return LazyMap(get_record, list(iids), size.total)

    def format_results(self, results):
        batch = HypermediaBatch(self.request, results)
        results = {}
        results["@id"] = batch.canonical_url
        results["items_total"] = batch.items_total
        links = batch.links
        if links:
            results["batching"] = links
        results["items"] = items = []
        for record in batch:
            item = dict(record.attrs)
            item["based_on"] = (
                self.serialize_item(item["based_on"]) if item["based_on"] else None
            )
            item["newsletter"] = self.serialize_item(item["newsletter"])
            items.append(json_compatible(item))
        return results

    def serialize_item(self, uid: str):
        brain = uuidToCatalogBrain(uid)
        return {
            "@id": brain.getURL(),
            "title": brain.Title,
        }


@implementer(ICatalogFactory)
class MailingCatalogFactory:
    def __call__(self, context=None):
        catalog = Catalog()
        catalog["sent_at"] = CatalogFieldIndex(NodeAttributeIndexer("sent_at"))
        catalog["newsletter"] = CatalogFieldIndex(NodeAttributeIndexer("newsletter"))
        catalog["based_on"] = CatalogFieldIndex(NodeAttributeIndexer("based_on"))
        return catalog
