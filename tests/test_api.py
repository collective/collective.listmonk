import pytest


class TestSubscriptionsService:
    @pytest.fixture(autouse=True)
    def load_functional_layer(self, functional):
        pass

    def test_create_subscription(
        self, newsletter, anon_plone_client, mailhog_client, listmonk_client
    ):
        subscriptions_url = f"{newsletter.absolute_url()}/@subscriptions"
        response = anon_plone_client.post(
            subscriptions_url,
            json={
                "email": "test@example.com",
            },
        )
        assert response.status_code == 200

        # Assert confirmation email was sent
        # resp = mailhog_client.get("/messages")
        # messages = resp.json()
        # assert len(messages) == 1

        # Assert unconfirmed subscription was created in listmonk
        resp = listmonk_client.get(
            "/subscribers", params={"list_id": [newsletter.listmonk_id]}
        )
        subscriber = [
            s
            for s in resp.json()["data"]["results"]
            if s["email"] == "test@example.com"
        ][0]
        subscription = [
            lst for lst in subscriber["lists"] if lst["id"] == newsletter.listmonk_id
        ][0]
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
