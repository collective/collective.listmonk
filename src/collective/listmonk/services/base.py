from plone import api
from plone.dexterity.content import DexterityContent
from plone.restapi.services import Service
from typing import TypeVar
from zExceptions import BadRequest

import json
import pydantic


T = TypeVar("T", bound=pydantic.BaseModel)


class PydanticService(Service):
    def validate_params(self, model: type[T]) -> T:
        try:
            return model.model_validate(self.request.form)
        except pydantic.ValidationError as exc:
            raise self._error(exc)

    def validate_body(self, model: type[T]) -> T:
        try:
            return model.model_validate_json(self.request.get("BODY"))
        except pydantic.ValidationError as exc:
            raise self._error(exc)

    def _error(self, exc: pydantic.ValidationError):
        return BadRequest(
            json.dumps(
                [
                    {"message": error["msg"], "field": error["loc"][-1]}
                    for error in exc.errors()
                ]
            )
        )


def deserialize_obj_link(s) -> DexterityContent:
    if isinstance(s, dict):
        s = s.get("@id")
    if not s or not isinstance(s, str):
        raise ValueError("Invalid URL")
    portal = api.portal.get()
    portal_url = portal.absolute_url()
    obj = None
    if s.startswith(portal_url):
        # Resolve by URL
        obj = portal.restrictedTraverse(s[len(portal_url) + 1 :], None)
    elif s.startswith("/"):
        # Resolve by path
        obj = portal.restrictedTraverse(s.lstrip("/"), None)
    if obj is None:
        raise ValueError("Content not found.")
    return obj
