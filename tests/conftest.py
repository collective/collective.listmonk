from collective.listmonk.testing import FUNCTIONAL_TESTING
from collective.listmonk.testing import INTEGRATION_TESTING
from pathlib import Path
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.restapi.testing import RelativeSession
from pytest_plone import fixtures_factory
from pythongettext.msgfmt import Msgfmt
from pythongettext.msgfmt import PoSyntaxError
from typing import Generator

import pytest
import transaction


pytest_plugins = ["pytest_plone"]


globals().update(
    fixtures_factory(
        (
            (FUNCTIONAL_TESTING, "functional"),
            (INTEGRATION_TESTING, "integration"),
        )
    )
)


@pytest.fixture(scope="session", autouse=True)
def generate_mo():
    """Generate .mo files."""
    import collective.listmonk

    locales_path = Path(collective.listmonk.__file__).parent / "locales"
    po_files: Generator = locales_path.glob("**/*.po")
    for po_file in po_files:
        parent: Path = po_file.parent
        domain: str = po_file.name[: -len(po_file.suffix)]
        mo_file: Path = parent / f"{domain}.mo"
        try:
            mo = Msgfmt(f"{po_file}", name=domain).getAsFile()
        except PoSyntaxError:
            continue
        else:
            with open(mo_file, "wb") as f_out:
                f_out.write(mo.read())


@pytest.fixture()
def portal(functional):
    return functional["portal"]


@pytest.fixture()
def newsletter(portal):
    with api.env.adopt_roles(["Manager"]):
        newsletter = api.content.create(
            type="Newsletter",
            container=portal,
            title="Test Newsletter",
            topics=[{"title": "Test topic", "list_id": "1"}],
            email_from_name="collective.listmonk tests",
            email_header="(header)",
            email_footer="(footer)",
        )
        api.content.transition(newsletter, "publish")
        transaction.commit()
        return newsletter


def make_api_session(portal):
    url = portal.absolute_url()
    api_session = RelativeSession(url)
    api_session.headers.update({"Accept": "application/json"})
    return api_session


@pytest.fixture()
def anon_plone_client(portal):
    return make_api_session(portal)


@pytest.fixture()
def manager_plone_client(portal):
    api_session = make_api_session(portal)
    api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
    return api_session


@pytest.fixture()
def listmonk_client():
    session = RelativeSession("http://localhost:9000/api")
    session.auth = ("admin", "admin")
    return session


@pytest.fixture()
def mailhog_client():
    return RelativeSession("http://localhost:8025/api/v1")
