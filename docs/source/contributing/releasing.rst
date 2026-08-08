Releasing
=========

fountain-py publishes to PyPI and deploys its docs automatically when you cut a GitHub Release.
You never handle a PyPI token: publishing uses PyPI trusted publishing over OIDC.

How a Release Works
-------------------

Publishing a GitHub Release (the ``release: published`` event) fires two workflows:

- ``.github/workflows/publish.yml`` builds the package and runs ``uv publish``, which authenticates to PyPI through the repository's OIDC identity and uploads the wheel and sdist.
- ``.github/workflows/docs.yml`` builds the Sphinx docs and deploys them to GitHub Pages.

The publish job runs only after its ``test`` and ``build`` jobs pass. It runs in the ``pypi`` deployment environment with ``id-token: write``, which is what lets PyPI trust it.

Cutting a Release
-----------------

1. Make sure ``main`` is green and holds the code you want to ship.
2. Bump ``version`` under ``[project]`` in ``pyproject.toml`` to the new version, and merge that to ``main``.
3. Create a GitHub Release whose tag is the version prefixed with ``v`` (for example ``v0.1.0``), targeting ``main``:

   .. code-block:: bash

      gh release create v0.1.0 --target main --title "v0.1.0" --generate-notes

   Publishing the Release is what triggers the workflows. A plain tag push does not.

Verifying
---------

Watch the runs, then confirm the results:

.. code-block:: bash

   gh run watch

- Package: https://pypi.org/project/fountain-py/
- Docs: https://masonegger.github.io/fountain-py/

Install the published version in a clean environment to smoke-test it:

.. code-block:: bash

   pip install fountain-py

One-Time Setup
--------------

These are already configured.
This section records them so a new maintainer can reproduce them.

- **PyPI trusted publisher** for the ``fountain-py`` project: owner ``MasonEgger``, repository ``fountain-py``, workflow ``publish.yml``, environment ``pypi``. Before the first release the project does not exist on PyPI, so this is added as a *pending publisher* under `PyPI account publishing <https://pypi.org/manage/account/publishing/>`_. The first successful publish creates the project and activates the publisher.
- **GitHub environments**: ``pypi`` (used by ``publish.yml``) and ``github-pages`` (used by ``docs.yml``).
- **GitHub Pages**: enabled with GitHub Actions as the build source. The ``github-pages`` environment allows deployments from ``main`` and from ``v*`` tags, so both the push-to-main and the release-triggered docs deploys succeed.

Troubleshooting
---------------

- **The publish step returns 403.** PyPI has no trusted publisher matching the upload.
  Confirm the publisher's project name reads ``fountain-py`` and that the owner, repository, workflow filename (``publish.yml``), and environment (``pypi``) all match.
- **The release-triggered docs deploy fails while the push-to-main deploy succeeded.** The ``github-pages`` environment is rejecting the tag ref.
  Add a deployment branch policy that allows ``v*`` tags.
