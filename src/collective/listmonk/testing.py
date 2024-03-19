from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing.layer import Layer
from plone.testing.zope import WSGI_SERVER_FIXTURE

import collective.listmonk
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).parent.parent.parent.parent


class ListmonkLayer(Layer):
    """Runs listmonk in a container"""

    def setUp(self):
        self.proc = subprocess.call(
            "docker compose -p listmonk_test -f docker-compose.yml up --wait",
            shell=True,
            close_fds=True,
            cwd=ROOT,
        )

    def tearDown(self):
        subprocess.call(
            "docker compose -p listmonk_test -f docker-compose.yml down",
            shell=True,
            close_fds=True,
            cwd=ROOT,
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


FIXTURE = Layer()

INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="Collective.ListmonkLayer:IntegrationTesting",
)


FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE, WSGI_SERVER_FIXTURE, LISTMONK_FIXTURE),
    name="Collective.ListmonkLayer:FunctionalTesting",
)
