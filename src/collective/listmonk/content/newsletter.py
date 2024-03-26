from collective.listmonk import _
from plone.dexterity.content import Container
from plone.supermodel.model import Schema
from zope import schema
from zope.interface import implementer


class INewsletter(Schema):
    """A Listmonk newsletter."""

    listmonk_id = schema.Int(
        title=_("Listmonk newsletter id"),
        required=True,
    )


@implementer(INewsletter)
class Newsletter(Container):
    """A newsletter."""
