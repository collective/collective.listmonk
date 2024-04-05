from collective.listmonk import _
from email.utils import formataddr
from plone import api
from plone.dexterity.content import Container
from plone.schema import JSONField
from plone.supermodel.model import Schema
from zope import schema
from zope.interface import implementer

import json


class INewsletter(Schema):
    """A Listmonk newsletter."""

    topics = JSONField(
        title=_("label_topics", "Topics"),
        schema=json.dumps(
            {
                "type": "array",
                "items": {
                    "title": "Topic",
                    "type": "object",
                    "fieldsets": [
                        {
                            "id": "default",
                            "title": "Default",
                            "fields": ["title", "list_id"],
                        },
                    ],
                    "properties": {
                        "title": {"title": "Topic", "type": "string"},
                        "list_id": {"title": "List ID", "type": "string"},
                    },
                },
            }
        ),
        default=[],
        widget="json_list",
    )

    from_name = schema.TextLine(
        title=_("label_from_name", default="E-Mail Sender Name (From)"),
        required=False,
    )


@implementer(INewsletter)
class Newsletter(Container):
    """A newsletter."""

    def get_email_sender(self):
        from_address = api.portal.get_registry_record("plone.email_from_address")
        from_name = self.from_name or api.portal.get_registry_record(
            "plone.email_from_name"
        )
        return formataddr((from_name, from_address))
