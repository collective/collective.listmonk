from plone.restapi.services import Service
from typing import TypeVar
from zExceptions import BadRequest

import json
import pydantic


T = TypeVar("T", bound=pydantic.BaseModel)


class PydanticService(Service):
    def validate(self, model: type[T]) -> T:
        try:
            return model.model_validate_json(self.request.get("BODY"))
        except pydantic.ValidationError as exc:
            raise BadRequest(
                json.dumps(
                    [
                        {"message": error["msg"], "field": error["loc"][-1]}
                        for error in exc.errors()
                    ]
                )
            )
