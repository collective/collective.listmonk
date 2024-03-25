import email
import pytest
import time


class TestMailingsService:
    list_id = 1

    @pytest.fixture(autouse=True)
    def load_functional_layer(self, functional):
        pass

    @pytest.fixture()
    def url(self, newsletter):
        return f"{newsletter.absolute_url()}/@mailings"

    def test_send_mailing(self, url, manager_plone_client, mailhog_client):
        response = manager_plone_client.post(
            url,
            json={
                "subject": "Test mailing",
                "body": "This is a test of the emergency broadcast system.",
            },
        )
        assert response.status_code == 200

        # Assert email was sent
        messages = poll_for_mail(mailhog_client, 2)
        msg = email.message_from_string(
            messages[1]["Raw"]["Data"], policy=email.policy.default
        )
        breakpoint()

    def test_send_mailing_test(self):
        pass


def poll_for_mail(mailhog_client, expected=1, retries=15):
    orig_retries = retries
    while retries > 0:
        messages = mailhog_client.get("/messages").json()
        if len(messages) == expected:
            return messages
        retries -= 1
        time.sleep(1)
    raise Exception(f"Timed out waiting for mail after {orig_retries}s")
