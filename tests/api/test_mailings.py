import email
import pytest
import time


class TestNewsletterMailingsService:
    list_id = 1

    @pytest.fixture(autouse=True)
    def load_functional_layer(self, functional):
        pass

    @pytest.fixture()
    def url(self, portal):
        return f"{portal.absolute_url()}/@mailings"

    def _send_mailing(self, url, newsletter, manager_plone_client):
        response = manager_plone_client.post(
            url,
            json={
                "subject": "Test mailing",
                "body": "This is a test of the emergency broadcast system.",
                "lists": [newsletter.absolute_url()],
            },
        )
        assert response.status_code == 200

    def test_send_mailing(self, url, newsletter, manager_plone_client, mailhog_client):
        self._send_mailing(url, newsletter, manager_plone_client)

        # Assert email was sent
        messages = poll_for_mail(mailhog_client, 2)
        msg = email.message_from_string(
            messages[1]["Raw"]["Data"], policy=email.policy.default
        )
        assert msg["To"] == "john@example.com"
        assert msg["Subject"] == "Test mailing"
        assert msg["Content-Type"] == 'text/plain; charset="UTF-8"'
        assert msg.get_content() == "This is a test of the emergency broadcast system."
        assert "List-Unsubscribe" not in msg

    def test_send_mailing_test(self):
        pass

    def test_get_mailings_for_newsletter(
        self, url, portal, newsletter, manager_plone_client
    ):
        self._send_mailing(url, newsletter, manager_plone_client)

        response = manager_plone_client.get(
            url,
            params={"list": newsletter.absolute_url()},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["items_total"] == 1
        item = result["items"][0]
        assert item["lists"][0]["@id"] == newsletter.absolute_url()
        assert item["lists"][0]["title"] == newsletter.title
        assert item["context"]["@id"] == portal.absolute_url()
        assert item["sent_by"] == "admin"
        assert item["subject"] == "Test mailing"
        assert "sent_at" in item

    def test_get_mailings_for_source_content(
        self, url, portal, newsletter, manager_plone_client
    ):
        self._send_mailing(url, newsletter, manager_plone_client)

        response = manager_plone_client.get(
            url, params={"context": portal.absolute_url()}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["items_total"] == 1
        item = result["items"][0]
        assert item["lists"][0]["@id"] == newsletter.absolute_url()
        assert item["lists"][0]["title"] == newsletter.title
        assert item["context"]["@id"] == portal.absolute_url()
        assert item["sent_by"] == "admin"
        assert item["subject"] == "Test mailing"
        assert "sent_at" in item


def poll_for_mail(mailhog_client, expected=1, retries=15):
    orig_retries = retries
    while retries > 0:
        messages = mailhog_client.get("/messages").json()
        if len(messages) == expected:
            return messages
        retries -= 1
        time.sleep(1)
    raise Exception(f"Timed out waiting for mail after {orig_retries}s")
