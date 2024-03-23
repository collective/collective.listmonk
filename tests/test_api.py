from collective.listmonk.services.subscriptions import get_subscriber

import email
import json
import pytest


class TestSubscriptionsService:
    list_id = 1

    @pytest.fixture(autouse=True)
    def load_functional_layer(self, functional):
        pass

    def test_create_subscription(
        self, portal, anon_plone_client, mailhog_client, listmonk_client
    ):
        subscriptions_url = f"{portal.absolute_url()}/@subscriptions"
        response = anon_plone_client.post(
            subscriptions_url,
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
        assert msg["To"] == "subscriber@example.com"
        # body = msg.get_content()
        # TODO parse token

        # Assert unconfirmed subscription was created in listmonk
        subscriber = get_subscriber("subscriber@example.com")
        subscription = [
            lst for lst in subscriber["lists"] if lst["id"] == self.list_id
        ][0]
        assert subscription["subscription_status"] == "unconfirmed"

    def test_create_subscription_again(self, portal, anon_plone_client, mailhog_client):
        # Trying to create it a second time re-sends the confirmation.
        subscriptions_url = f"{portal.absolute_url()}/@subscriptions"
        response = anon_plone_client.post(
            subscriptions_url,
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

    def test_create_subscription__bad_request(self, portal, anon_plone_client):
        subscriptions_url = f"{portal.absolute_url()}/@subscriptions"
        response = anon_plone_client.post(
            subscriptions_url,
            json={},
        )
        assert response.status_code == 400
        # Make sure it's in the format that volto expects
        assert json.loads(response.json()["message"])[0]["message"] == "Field required"

    def test_confirm_subscription(self, newsletter, anon_plone_client):
        pass

    def test_unsubscribe(self, newsletter, anon_plone_client):
        pass
