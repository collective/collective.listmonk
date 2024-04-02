from collective.listmonk import _
from plone.dexterity.content import Container
from plone.schema import JSONField
from plone.supermodel.model import Schema
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


@implementer(INewsletter)
class Newsletter(Container):
    """A newsletter."""
