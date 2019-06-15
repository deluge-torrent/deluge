# Launchpad recipe

The launchpad build recipes are for build from source automatically to provide
Ubuntu packages. They are used to create daily builds of a Deluge git branch.

Note these don't have the same control as a creating a publishing to PPA.

Main reference: <https://help.launchpad.net/Packaging/SourceBuilds/Recipes>

## Deluge Launchpad build recipes

Recipe configuration: <https://code.launchpad.net/~deluge-team/+recipes>

An example for building the develop branch:

    # git-build-recipe format 0.4 deb-version 2.0.0.dev{revno}+{git-commit}+{time}
    lp:deluge develop
    nest-part packaging lp:~calumlind/+git/lp_deluge_deb debian debian develop

There are two parts, first to get the source code branch and then the `debian`
files for building the package.

## Testing and building locally

Create a `deluge.recipe` file with the contents from launchpad and create the
build files with `git-build-recipe`:

    git-build-recipe --allow-fallback-to-native deluge.recipe lp_build

Setup [pbuilder] and build the deluge package:

    sudo pbuilder build lp_build/deluge*.dsc

Alternatively to build using local files with [pdebuild]:

    cd lp_build/deluge/deluge
    pdebuild

This will allow modifying the `debian` files to test changes to `rules` or
`control`.

[pbuilder]: https://wiki.ubuntu.com/PbuilderHowto
[pdebuild]: https://wiki.ubuntu.com/PbuilderHowto#pdebuild
