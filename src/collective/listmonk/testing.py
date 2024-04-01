from collective.listmonk import listmonk
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.base.interfaces.controlpanel import IMailSchema
from plone.registry.interfaces import IRegistry
from plone.testing.layer import Layer
from plone.testing.zope import WSGI_SERVER_FIXTURE
from zope.component import getUtility

import collective.listmonk
import subprocess


class ListmonkLayer(Layer):
    """Runs listmonk in a container"""

    def setUp(self):
        self.proc = subprocess.call(
            "docker compose -p listmonk_test -f docker-compose.yml up --wait",
            shell=True,
            close_fds=True,
        )

        # Configure SMTP server; disable unsubscribe headers
        settings = listmonk.call_listmonk("get", "/settings")["data"]
        smtp = settings["smtp"][0]
        smtp.update(
            {
                "enabled": True,
                "host": "mailhog",
                "port": 1025,
                "auth_protocol": "none",
                "tls_type": "none",
            }
        )
        settings.update({"smtp": [smtp], "privacy.unsubscribe_header": False})
        listmonk.call_listmonk("put", "/settings", json=settings)

        # Configure template
        listmonk.call_listmonk(
            "put",
            "/templates/1",
            json={
                "name": "Default campaign template",
                "type": "campaign",
                "body": '{{ template "content" . }}',
            },
        )

    def tearDown(self):
        subprocess.call(
            "docker compose -p listmonk_test -f docker-compose.yml down",
            shell=True,
            close_fds=True,
        )


LISTMONK_FIXTURE = ListmonkLayer()


class Layer(PloneSandboxLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi
        import plone.volto

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=plone.volto)
        self.loadZCML(package=collective.listmonk)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.volto:default")
        applyProfile(portal, "collective.listmonk:default")

        registry = getUtility(IRegistry)
        mail_settings = registry.forInterface(IMailSchema, prefix="plone")
        mail_settings.email_from_name = "Test Plone"
        mail_settings.email_from_address = "testplone@example.com"
        mail_settings.smtp_host = "localhost"
        mail_settings.smtp_port = 1025


FIXTURE = Layer()

INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="Collective.ListmonkLayer:IntegrationTesting",
)


FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE, WSGI_SERVER_FIXTURE, LISTMONK_FIXTURE),
    name="Collective.ListmonkLayer:FunctionalTesting",
)
