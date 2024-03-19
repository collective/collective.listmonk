from collective.listmonk import PACKAGE_NAME

import requests


class TestSetupInstall:
    def test_addon_installed(self, installer):
        """Test if add-on is installed."""
        assert installer.is_product_installed(PACKAGE_NAME) is True

    def test_browserlayer(self, browser_layers):
        """Test that IBrowserLayer is registered."""
        from collective.listmonk.interfaces import IBrowserLayer

        assert IBrowserLayer in browser_layers

    def test_latest_version(self, profile_last_version):
        """Test latest version of default profile."""
        assert profile_last_version(f"{PACKAGE_NAME}:default") == "1000"

    def test_listmonk_version(self, functional):
        response = requests.get(
            "http://localhost:9000/api/config", auth=("admin", "admin")
        )
        assert response.status_code == 200
        assert response.json()["data"]["version"] == "v3.0.0"
