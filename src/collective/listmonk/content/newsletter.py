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

    confirm_email_subject = schema.TextLine(
        title=_("label_confirm_email_subject", default="Confirmation E-mail Subject"),
        default=_(
            "default_confirm_email_subject", default="Confirm {newsletter} subscription"
        ),
        required=True,
    )

    confirm_email_body = schema.Text(
        title=_("label_confirm_email_body", default="Confirmation E-mail Body"),
        default=_(
            "default_confirm_email_body",
            default="""Thank you for subscribing to the {newsletter}.

To confirm your subscription, please click on this link:
{confirm_link}

If you have not requested this subscription, you can ignore this e-mail.
""",
        ),
        required=True,
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
        parts = [content]

        request = getRequest()
        parts.append(
            translate(
                _(
                    "email_mailing_footer",
                    default="---\nTo unsubscribe, please click on the following link:\n${unsubscribe_link}",
                    mapping={"unsubscribe_link": self.get_unsubscribe_link()},
                ),
                request,
            )
        )

        return "\n\n".join(parts)

    def get_unsubscribe_link(self):
        request = getRequest()
        unsubscribe_path = translate(
            _("path_unsubscribe", default="newsletter-unsubscribe"),
            context=request,
        )
        return f"{self.absolute_url()}/{unsubscribe_path}"
