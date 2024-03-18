from collective.listmonk.testing import ACCEPTANCE_TESTING
from collective.listmonk.testing import FUNCTIONAL_TESTING
from collective.listmonk.testing import INTEGRATION_TESTING
from pathlib import Path
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.restapi.testing import RelativeSession
from pytest_plone import fixtures_factory
from pythongettext.msgfmt import Msgfmt
from pythongettext.msgfmt import PoSyntaxError
from typing import Generator

import pytest


pytest_plugins = ["pytest_plone"]


globals().update(
    fixtures_factory(
        (
            (ACCEPTANCE_TESTING, "acceptance"),
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
def request_factory(portal):
    def factory():
        url = portal.absolute_url()
        api_session = RelativeSession(url)
        api_session.headers.update({"Accept": "application/json"})
        return api_session

    return factory


@pytest.fixture()
def anon_request(request_factory):
    return request_factory()


@pytest.fixture()
def manager_request(request_factory):
    request = request_factory()
    request.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
    yield request
    request.auth = ()
