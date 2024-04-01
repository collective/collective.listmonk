from collective.listmonk import _
from collective.listmonk import listmonk
from collective.listmonk.content.newsletter import Newsletter
from collective.listmonk.services.base import deserialize_obj_link
from collective.listmonk.services.base import PydanticService
from datetime import datetime
from plone import api
from plone.app.uuid.utils import uuidToCatalogBrain
from plone.restapi.batching import HypermediaBatch
from plone.restapi.interfaces import ISerializeToJsonSummary
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
from typing import Optional
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import implementer
from ZTUtils.Lazy import LazyMap

import pydantic
import transaction


MAILINGS_SOUP = "collective.listmonk.mailings"


class MailingRequest(pydantic.BaseModel):
    subject: str
    body: str
    list_ids: list[int]
    based_on: Optional[str]


class SendMailing(PydanticService):
    context: Newsletter

    def reply(self):
        data = self.validate_body(MailingRequest)

        if data.based_on:
            based_on = deserialize_obj_link(data.based_on)

        list_ids = list(set(data.list_ids).intersection(self.context.topics.values()))
        topics = [k for k, v in self.context.topics.items() if v in list_ids]

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
        get_soup(MAILINGS_SOUP, self.context).add(record)
        transaction.commit()

        unsubscribe_path = translate(
            _("path_unsubscribe", default="unsubscribe"), context=self.request
        )
        unsubscribe_link = f"{self.context.absolute_url()}/{unsubscribe_path}"
        body = data.body + translate(
            _(
                "email_mailing_footer",
                default="""

Unsubscribe: ${unsubscribe_link}
""",
                mapping={"unsubscribe_link": unsubscribe_link},
            ),
            self.request,
        )

        # Create campaign in listmonk
        result = listmonk.call_listmonk(
            "post",
            "/campaigns",
            json={
                "name": data.subject,
                "subject": data.subject,
                "lists": list_ids,
                "type": "regular",
                "content_type": "plain",
                "body": body,
            },
        )
        campaign = result["data"]

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
            query = NotEq("sent_at", 0)
        return query

    def run_query(self, queryobject, sort_index=None, reverse=False):
        soup = get_soup(MAILINGS_SOUP, self.context)
        size, iids = soup.catalog.query(
            queryobject,
            sort_index=sort_index,
            reverse=reverse,
        )

        def get_record(i):
            return soup.data[i]

        return LazyMap(get_record, list(iids), size)

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
        obj = uuidToCatalogBrain(uid)
        serializer = getMultiAdapter((obj, self.request), ISerializeToJsonSummary)
        return serializer()


@implementer(ICatalogFactory)
class MailingCatalogFactory:
    def __call__(self, context=None):
        catalog = Catalog()
        catalog["sent_at"] = CatalogFieldIndex(NodeAttributeIndexer("sent_at"))
        catalog["newsletter"] = CatalogFieldIndex(NodeAttributeIndexer("newsletter"))
        catalog["based_on"] = CatalogFieldIndex(NodeAttributeIndexer("based_on"))
        return catalog
