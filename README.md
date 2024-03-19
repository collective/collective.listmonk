<p align="center">
    <img alt="kitconcept GmbH" width="200px" src="https://kitconcept.com/logo.svg">
</p>

<h1 align="center">collective.listmonk</h1>
<h3 align="center">Listmonk newsletter integration for Plone</h3>

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/collective.listmonk)](https://pypi.org/project/collective.listmonk/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/collective.listmonk)](https://pypi.org/project/collective.listmonk/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/collective.listmonk)](https://pypi.org/project/collective.listmonk/)
[![PyPI - License](https://img.shields.io/pypi/l/collective.listmonk)](https://pypi.org/project/collective.listmonk/)
[![PyPI - Status](https://img.shields.io/pypi/status/collective.listmonk)](https://pypi.org/project/collective.listmonk/)

[![PyPI - Plone Versions](https://img.shields.io/pypi/frameworkversions/plone/collective.listmonk)](https://pypi.org/project/collective.listmonk/)

[![Meta](https://github.com/collective/collective.listmonk/actions/workflows/meta.yml/badge.svg)](https://github.com/collective/collective.listmonk/actions/workflows/meta.yml)
![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000)

[![GitHub contributors](https://img.shields.io/github/contributors/collective/collective.listmonk)](https://github.com/collective/collective.listmonk)
[![GitHub Repo stars](https://img.shields.io/github/stars/collective/collective.listmonk?style=social)](https://github.com/collective/collective.listmonk)

</div>

## Features

`collective.listmonk` adds the ability to send email newsletters from a [Plone](https://plone.org/) site.

### Content Types

| name         | context                            |
| ------------ | ---------------------------------- |
| `Newsletter` | Represents a Listmonk mailing list |

## Installation

Add `collective.listmonk` as a dependency in your package's `setup.py`

```python
    install_requires = [
        "collective.listmonk",
        "Plone",
        "plone.restapi",
        "setuptools",
    ],
```

Also, add `collective.listmonk` to your package's `configure.zcml` (or `dependencies.zcml`):

```xml
<include package="collective.listmonk" />
```

### Generic Setup

To automatically enable this package when your add-on is installed, add the following line inside the package's `profiles/default/metadata.xml` `dependencies` element:

```xml
    <dependency>profile-collective.listmonk:default</dependency>
```

## Source Code and Contributions

We welcome contributions to `collective.listmonk`.

You can create an issue in the issue tracker, or contact a maintainer.

- [Issue Tracker](https://github.com/collective/collective.listmonk/issues)
- [Source Code](https://github.com/collective/collective.listmonk/)

### Development requirements

- Python 3.11 or later
- Docker

### Setup

Install all development dependencies -- including Plone -- and create a new instance using:

```bash
make install
```

### Start Listmonk

```bash
make start-listmonk
```

This runs Listmonk at http://localhost:9000 and Mailhog at http://localhost:8025

### Start Plone

```bash
make start
```

### Update translations

```bash
make i18n
```

### Format codebase

```bash
make format
```

### Run tests

Testing of this package is done with [`pytest`](https://docs.pytest.org/) and [`tox`](https://tox.wiki/).

Run all tests with:

```bash
make test
```

Run all tests but stop on the first error and open a `pdb` session:

```bash
./bin/tox -e test -- -x --pdb
```

Run only tests that match `TestVocabAuthors`:

```bash
./bin/tox -e test -- -k TestVocabAuthors
```

Run only tests that match `TestVocabAuthors`, but stop on the first error and open a `pdb` session:

```bash
./bin/tox -e test -- -k TestVocabAuthors -x --pdb
```

## Credits

The development of this add-on has been kindly sponsored by [German Aerospace Center (DLR)](https://www.dlr.de).

<img alt="German Aerospace Center (DLR)" width="200px" src="https://raw.githubusercontent.com/collective/collective.listmonk/main/docs/dlr.svg" style="background-color:white">

Developed by [kitconcept](https://www.kitconcept.com/)

## License

The project is licensed under GPLv2.
