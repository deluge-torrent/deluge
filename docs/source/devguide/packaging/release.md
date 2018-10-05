# Release Checklist

## Pre-Release

- Update [translation](../contributing/translations.md) `po` files from
  [Launchpad](https://translations.launchpad.net/deluge) account.
- Changelog is updated with relevant commits and release date is added.
- Version number increment:
  - setup.py
  - man pages
  - osx/Info.plist
  - Version and month `sed` commands:
    - `git grep -l '2\.0\.0' | grep -v CHANGELOG.md | xargs sed -i 's/2\.0\.0/2\.0\.1/g'`
    - `git grep -l 'October' docs/man | xargs sed -i 's/October/November/g'`
- Increment copyright year:
  - osx/Info.plist
- Tag release in git and push upstream.
  - e.g. `git tag -a deluge-2.0.0 -m "Deluge 2.0.0 Release"`

## Release

- Run `make_release` script on extracted tarball e.g.
  - `make_release deluge-2.0.0`
- Package for OSs, Ubuntu, Windows, OSX.
- Upload source tarballs and packages to ftp.
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
