"""
Updates all outdated packages using pip. Also allows specifying packages, or
showing outdated packages.

## Usage

>    $ pip_upgrade -h
>    usage: Provides functionality for updating all your outdated packages
>
>    positional arguments:
>      PACKAGE_NAME          Name of package to update - without specifying a
>                            package all packages will be updated.
>
>    optional arguments:
>      -h, --help            show this help message and exit
>      -d, --dry, --dry-run  Do not do anything, just print what would be done.
"""
from .outdated_list import OutdatedList
from argparse import ArgumentParser


def main():
    parser = ArgumentParser('pip_upgrade',
                            'Provides functionality for updating all your ' +
                            'outdated packages')

    parser.add_argument('-d', '--dry', '--dry-run',
                        dest="dry_run", default=False,
                        action="store_true",
                        help="No install, just print what would be done.")

    parser.add_argument('packages', nargs='*',
                        metavar="PACKAGE_NAME",
                        help="Name of a package to update - without specifying "
                             "a package all packages will be updated.")

    options = parser.parse_args()

    outdated = OutdatedList(dry_run=options.dry_run)

    for name, local, remote in outdated.outdated:
        if (not options.packages) or name in options.packages:
            outdated.upgrade(name, local, remote)


if __name__ == '__main__':
    main()
