from collective.listmonk import _
from plone.dexterity.content import Container
from plone.supermodel.model import Schema
from zope import schema
from zope.interface import implementer


class INewsletter(Schema):
    """A Listmonk newsletter."""

    topics = schema.Dict(
        title=_("label_topics", "Topics"),
        key_type=schema.TextLine(title=_("label_topic", default="Topic")),
        value_type=schema.Int(title=_("label_list_id", default="Listmonk list id")),
        required=True,
    )


@implementer(INewsletter)
class Newsletter(Container):
    """A newsletter."""
