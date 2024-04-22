from ..conftest import poll_for_mail
from collective.listmonk import listmonk

import email
import pytest


class TestNewsletterMailingsService:
    list_id = 1

    @pytest.fixture(autouse=True)
    def load_functional_layer(self, functional):
        pass

    def _send_mailing(self, portal, newsletter, manager_plone_client):
        response = manager_plone_client.post(
            f"{newsletter.absolute_url()}/@mailings",
            json={
                "subject": "Test mailing",
                "body": """This is a test of the emergency broadcast system.""",
                "based_on": portal.absolute_url(),
                "list_ids": [self.list_id],
            },
        )
        assert response.status_code == 200

    def test_send_mailing(
        self, portal, newsletter, manager_plone_client, mailhog_client
    ):
        self._send_mailing(portal, newsletter, manager_plone_client)

        # Assert email was sent
        subscriber = listmonk.find_subscriber(email="john@example.com")
        messages = poll_for_mail(mailhog_client, 2)
        msg = email.message_from_string(
            messages[1]["Raw"]["Data"], policy=email.policy.default
        )
        assert msg["From"] == '"collective.listmonk tests" <testplone@example.com>'
        assert msg["To"] == "john@example.com"
        assert msg["Subject"] == "Test mailing"
        assert msg["Content-Type"] == 'text/plain; charset="UTF-8"'
        assert (
            msg.get_content()
            == f"""This is a test of the emergency broadcast system.

---
To unsubscribe, please click on the following link:
{newsletter.absolute_url()}/newsletter-unsubscribe?s={subscriber['uuid']}""".replace(
                "\n", "\r\n"
            )
        )
        assert "List-Unsubscribe" not in msg

    def test_send_mailing_test(
        self, portal, newsletter, manager_plone_client, mailhog_client
    ):
        response = manager_plone_client.post(
            f"{newsletter.absolute_url()}/@mailings",
            json={
                "subject": "Test mailing",
                "body": """This is a test of the emergency broadcast system.""",
                "based_on": portal.absolute_url(),
                "list_ids": [self.list_id],
                "send_test_to": ["anon@example.com"],
            },
        )
        assert response.status_code == 200

        # Assert email was sent
        subscriber = listmonk.find_subscriber(email="anon@example.com")
        messages = poll_for_mail(mailhog_client, 3)
        msg = email.message_from_string(
            messages[0]["Raw"]["Data"], policy=email.policy.default
        )
        assert msg["From"] == '"collective.listmonk tests" <testplone@example.com>'
        assert msg["To"] == "anon@example.com"
        assert msg["Subject"] == "Test mailing"
        assert msg["Content-Type"] == 'text/plain; charset="UTF-8"'
        assert (
            msg.get_content()
            == f"""This is a test of the emergency broadcast system.

---
To unsubscribe, please click on the following link:
{newsletter.absolute_url()}/newsletter-unsubscribe?s={subscriber['uuid']}""".replace(
                "\n", "\r\n"
            )
        )
        assert "List-Unsubscribe" not in msg

    def test_get_mailings_for_newsletter(
        self, portal, newsletter, manager_plone_client
    ):
        self._send_mailing(portal, newsletter, manager_plone_client)

        response = manager_plone_client.get(
            f"{portal.absolute_url()}/@mailings",
            params={"newsletter": newsletter.absolute_url()},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["items_total"] == 1
        item = result["items"][0]
        assert item["newsletter"]["@id"] == newsletter.absolute_url()
        assert item["newsletter"]["title"] == newsletter.title
        assert item["topics"] == ["Test topic"]
        assert item["based_on"]["@id"] == portal.absolute_url()
        assert item["sent_by"] == "admin"
        assert item["subject"] == "Test mailing"
        assert "sent_at" in item

    def test_get_mailings_for_source_content(
        self, portal, newsletter, manager_plone_client
    ):
        self._send_mailing(portal, newsletter, manager_plone_client)

        response = manager_plone_client.get(
            f"{portal.absolute_url()}/@mailings",
            params={"based_on": portal.absolute_url()},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["items_total"] == 1
        item = result["items"][0]
        assert item["newsletter"]["@id"] == newsletter.absolute_url()
        assert item["newsletter"]["title"] == newsletter.title
        assert item["topics"] == ["Test topic"]
        assert item["based_on"]["@id"] == portal.absolute_url()
        assert item["sent_by"] == "admin"
        assert item["subject"] == "Test mailing"
        assert "sent_at" in item
