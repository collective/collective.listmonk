from ..conftest import poll_for_mail
from collective.listmonk import listmonk
from urllib.parse import unquote

import email
import json
import pytest
import re


class TestSubscriptionsService:
    # Note: These tests are not independent and must run in order.

    list_id = 1

    @pytest.fixture(autouse=True)
    def load_functional_layer(self, functional):
        pass

    @pytest.fixture()
    def url(self, newsletter):
        return f"{newsletter.absolute_url()}/@subscriptions"

    def test_create_subscription(self, url, anon_plone_client, mailhog_client):
        response = anon_plone_client.post(
            url,
            json={
                "name": "Jean-Luc Picard",
                "email": "subscriber@example.com",
                "list_ids": [self.list_id],
            },
        )
        assert response.status_code == 200

        # Assert confirmation email was sent
        resp = mailhog_client.get("/messages")
        messages = resp.json()
        assert len(messages) == 1
        msg = email.message_from_string(
            messages[0]["Raw"]["Data"], policy=email.policy.default
        )
        assert msg["From"] == '"collective.listmonk tests" <testplone@example.com>'
        assert msg["To"] == "subscriber@example.com"

        # Assert unconfirmed subscription was created in listmonk
        subscriber = listmonk.find_subscriber(email="subscriber@example.com")
        subscription = [
            lst for lst in subscriber["lists"] if lst["id"] == self.list_id
        ][0]
        assert subscription["subscription_status"] == "unconfirmed"

    def test_create_subscription_again(
        self, newsletter, url, anon_plone_client, mailhog_client
    ):
        # Trying to create it a second time re-sends the confirmation.
        response = anon_plone_client.post(
            url,
            json={
                "name": "Jean-Luc Picard",
                "email": "subscriber@example.com",
                "list_ids": [self.list_id],
            },
        )
        assert response.status_code == 200

        # Assert confirmation email was sent
        resp = mailhog_client.get("/messages")
        messages = resp.json()
        assert len(messages) == 2
        msg = email.message_from_string(
            messages[0]["Raw"]["Data"], policy=email.policy.default
        )
        body = msg.get_content()
        token = unquote(re.search(r"token=(\S+)", body).group(1))

        # Confirm the subscription
        response = anon_plone_client.put(url, json={"token": token})
        assert response.status_code == 200

        # Confirm status was updated in listmonk
        subscriber = listmonk.find_subscriber(email="subscriber@example.com")
        subscription = [
            lst for lst in subscriber["lists"] if lst["id"] == self.list_id
        ][0]
        assert subscription["subscription_status"] == "confirmed"

        # Confirm email was sent to confirm subscription
        poll_for_mail(mailhog_client, 3)
        resp = mailhog_client.get("/messages")
        messages = resp.json()
        assert len(messages) == 3
        msg = email.message_from_string(
            messages[0]["Raw"]["Data"], policy=email.policy.default
        )
        body = msg.get_content()
        assert msg["From"] == '"collective.listmonk tests" <testplone@example.com>'
        assert msg["To"] == "subscriber@example.com"
        assert msg["Subject"] == "Subscription confirmed"
        assert msg["Content-Type"] == 'text/plain; charset="utf-8"'
        assert (
            msg.get_content()
            == f"""You are now subscribed to the Test Newsletter\r
\r
You can unsubscribe using this link:\r
{newsletter.absolute_url()}/newsletter-unsubscribe?s={subscriber['uuid']}"""
        )

    def test_create_subscription__bad_request(self, url, anon_plone_client):
        response = anon_plone_client.post(
            url,
            json={},
        )
        assert response.status_code == 400
        # Make sure it's in the format that volto expects
        assert json.loads(response.json()["message"])[0]["message"] == "Field required"

    def test_confirm_subscription__bad_token(self, url, anon_plone_client):
        response = anon_plone_client.put(
            url,
            json={"token": "BOGUS"},
        )
        assert response.status_code == 400

    def test_unsubscribe(self, url, anon_plone_client):
        subscriber = listmonk.find_subscriber(email="subscriber@example.com")
        response = anon_plone_client.delete(
            url,
            json={
                "sub_uuid": subscriber["uuid"],
                "list_ids": [self.list_id],
            },
        )
        assert response.status_code == 200

        subscriber = listmonk.find_subscriber(email="subscriber@example.com")
        assert subscriber is None

    def test_unsubscribe__unknown_email(self, url, anon_plone_client):
        response = anon_plone_client.delete(
            url,
            json={
                "email": "bogus@example.com",
                "list_ids": [self.list_id],
            },
        )
        assert response.status_code == 400
