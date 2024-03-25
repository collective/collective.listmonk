from collective.listmonk import listmonk
from collective.listmonk.content.newsletter import Newsletter
from collective.listmonk.services.base import PydanticService

import pydantic


class MailingRequest(pydantic.BaseModel):
    subject: str
    body: str


class SendMailing(PydanticService):
    context: Newsletter

    def reply(self):
        data = self.validate(MailingRequest)

        result = listmonk.call_listmonk(
            "post",
            "/campaigns",
            json={
                "name": data.subject,
                "subject": data.subject,
                "lists": [self.context.listmonk_id],
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
