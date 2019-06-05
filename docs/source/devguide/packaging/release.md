# Release Checklist

## Pre-Release

- Update [translation](../contributing/translations.md) `po` files from
  [Launchpad](https://translations.launchpad.net/deluge) account.
- Changelog is updated with relevant commits and release date is added.
- Tag release in git and push upstream.
  - e.g. `git tag -a deluge-2.0.0 -m "Deluge 2.0.0 Release"`

## Release

- Create source and wheel distributions:

        python setup.py sdist bdist_wheel

- Upload to PyPi:

        twine upload dist/deluge-2.0.0.tar.xz dist/deluge-2.0.0-py3-none-any.whl

- Package for OSs, Ubuntu, Windows, OSX.
- Upload source tarballs and packages.
  (_Ensure file permissions are global readable:_ `0644`)

## Post-Release

- Update with version, hashes and release notes:
  - ReleaseNotes (Create new version page and add link to this page)
  - Forum announcement
  - IRC welcome message
  - Website `index.php` and `version` files
  - [Wikipedia](http://en.wikipedia.org/wiki/Deluge_%28software%29)
- Trac close the milestone and add new version for tickets.
- Ensure all stable branch commits are also applied to development branch.
