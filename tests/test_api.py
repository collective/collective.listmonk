import email
import pytest


class TestSubscriptionsService:
    @pytest.fixture(autouse=True)
    def load_functional_layer(self, functional):
        pass

    def test_create_subscription(
        self, portal, anon_plone_client, mailhog_client, listmonk_client
    ):
        list_id = 1
        subscriptions_url = f"{portal.absolute_url()}/@subscriptions"
        response = anon_plone_client.post(
            subscriptions_url,
            json={
                "name": "Jean-Luc Picard",
                "email": "subscriber@example.com",
                "list_ids": [list_id],
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
        resp = listmonk_client.get("/subscribers", params={"list_id": [list_id]})
        subscriber = [
            s
            for s in resp.json()["data"]["results"]
            if s["email"] == "subscriber@example.com"
        ][0]
        subscription = [lst for lst in subscriber["lists"] if lst["id"] == list_id][0]
        assert subscription["subscription_status"] == "unconfirmed"

    def test_create_subscription_again(
        self, newsletter, anon_plone_client, mailhog_client, listmonk_client
    ):
        # Trying to create it a second time re-sends the confirmation.
        pass

    def test_confirm_subscription(self, newsletter, anon_plone_client):
        pass

    def test_unsubscribe(self, newsletter, anon_plone_client):
        pass
