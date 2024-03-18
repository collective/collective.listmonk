from plone.dexterity.content import Container
from zope.interface import implementer
from zope.interface import Interface


class INewsletter(Interface):
    """A newsletter."""


@implementer(INewsletter)
class Newsletter(Container):
    """A newsletter."""
