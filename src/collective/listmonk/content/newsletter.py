from collective.listmonk import _
from email.utils import formataddr
from plone import api
from plone.dexterity.content import Container
from plone.schema import JSONField
from plone.supermodel.model import Schema
from zope import schema
from zope.globalrequest import getRequest
from zope.i18n import translate
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

    email_from_name = schema.TextLine(
        title=_("label_email_from_name", default="E-mail Sender Name (From)"),
        required=False,
    )

    email_header = schema.Text(
        title=_("label_email_header", default="E-mail Header"),
        required=False,
    )

    email_footer = schema.Text(
        title=_("label_email_footer", default="E-mail Footer"),
        required=False,
    )


@implementer(INewsletter)
class Newsletter(Container):
    """A newsletter."""

    def get_email_sender(self):
        from_address = api.portal.get_registry_record("plone.email_from_address")
        from_name = self.email_from_name or api.portal.get_registry_record(
            "plone.email_from_name"
        )
        return formataddr((from_name, from_address))

    def get_email_body(self, content):
        parts = [self.email_header] if self.email_header else []
        parts.append(content)
        if self.email_footer:
            parts.append(self.email_footer)

        request = getRequest()
        unsubscribe_path = translate(
            _("path_unsubscribe", default="newsletter-unsubscribe"),
            context=request,
        )
        unsubscribe_link = f"{self.absolute_url()}/{unsubscribe_path}"
        parts.append(
            translate(
                _(
                    "email_mailing_footer",
                    default="---\nUnsubscribe: ${unsubscribe_link}",
                    mapping={"unsubscribe_link": unsubscribe_link},
                ),
                request,
            )
        )

        return "\n\n".join(parts)
