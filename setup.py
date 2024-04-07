"""Setuptools configuration for the collective.listmonk package."""

from pathlib import Path
from setuptools import find_packages
from setuptools import setup


long_description = f"""
{Path("README.md").read_text()}\n
{Path("CONTRIBUTORS.md").read_text()}\n
{Path("CHANGES.md").read_text()}\n
"""


setup(
    name="collective.listmonk",
    version="1.0.0a1",
    description="A Listmonk newsletter integration for Plone.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone CMS",
    author="kitconcept GmbH",
    author_email="info@kitconcept.com",
    url="https://github.com/collective/collective.listmonk",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/collective.listmonk",
        "Source": "https://github.com/collective/collective.listmonk",
        "Tracker": "https://github.com/collective/collective.listmonk/issues",
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["collective"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.11",
    install_requires=[
        "setuptools",
        "annotated-types",
        "Products.CMFPlone",
        "plone.api",
        "plone.restapi",
        "pydantic",
        "pydantic-settings",
        "requests",
        "souper.plone",
    ],
    extras_require={
        "test": [
            "zest.releaser[recommended]",
            "zestreleaser.towncrier",
            "plone.app.testing",
            "plone.restapi[test]",
            "plone.volto",
            "pytest",
            "pytest-cov",
            "pytest-plone>=0.2.0",
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = collective.listmonk.locales.update:update_locale
    """,
)
