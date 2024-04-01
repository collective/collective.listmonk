from annotated_types import Len
from collective.listmonk import listmonk
from collective.listmonk.services.base import deserialize_obj_link
from collective.listmonk.services.base import PydanticService
from datetime import datetime
from plone import api
from plone.app.uuid.utils import uuidToCatalogBrain
from plone.dexterity.content import DexterityContent
from plone.restapi.batching import HypermediaBatch
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.converters import json_compatible
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
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
from zope.component import getMultiAdapter
from zope.interface import implementer
from ZTUtils.Lazy import LazyMap

import pydantic
import transaction


MAILINGS_SOUP = "collective.listmonk.mailings"


class MailingRequest(pydantic.BaseModel):
    subject: str
    body: str
    lists: Annotated[list[str], Len(min_length=1)]


class SendMailing(PydanticService):
    context: DexterityContent

    def reply(self):
        data = self.validate_body(MailingRequest)

        lists = []
        for list_url in data.lists:
            try:
                lists.append(deserialize_obj_link(list_url))
            except ValueError:
                raise BadRequest(f"Invalid list URL: {list_url}")

        # Store mailing in Plone
        # (do this first so we only send the email once if there's a conflict error)
        record = Record()
        record.attrs.update(
            {
                "subject": data.subject,
                "lists": [list.UID() for list in lists],
                "sent_at": datetime.now(),
                "sent_by": api.user.get_current().getUserId(),
                "context": self.context.UID(),
            }
        )
        get_soup(MAILINGS_SOUP, self.context).add(record)
        transaction.commit()

        # Create campaign in listmonk
        result = listmonk.call_listmonk(
            "post",
            "/campaigns",
            json={
                "name": data.subject,
                "subject": data.subject,
                "lists": [list.listmonk_id for list in lists],
                "type": "regular",
                "content_type": "plain",
                "body": data.body,
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
    context: Optional[str] = None
    list: Optional[str] = None


class ListMailings(PydanticService):
    def reply(self):
        query = self.parse_query()
        results = self.run_query(query, sort_index="sent_at", reverse=True)
        return self.format_results(results)

    def parse_query(self):
        params = self.validate_params(MailingsQuery)
        criteria = []
        if params.context:
            criteria.append(Eq("context", deserialize_obj_link(params.context).UID()))
        if params.list:
            criteria.append(Eq("lists", deserialize_obj_link(params.list).UID()))
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
            item["context"] = self.serialize_item(item["context"])
            item["lists"] = [self.serialize_item(uid) for uid in item["lists"]]
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
        catalog["context"] = CatalogFieldIndex(NodeAttributeIndexer("context"))
        catalog["lists"] = CatalogKeywordIndex(NodeAttributeIndexer("lists"))
        return catalog
