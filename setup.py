"""Set up junifer package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from setuptools import setup


def _getversion():
    from setuptools_scm.version import (
        get_local_node_and_date,
        simplified_semver_version,
    )

    def clean_scheme(version):
        print(version)
        return get_local_node_and_date(version) if version.dirty else ""

    return {
        'version_scheme': simplified_semver_version,
        'local_scheme': clean_scheme,
        'write_to': 'junifer/_version.py',
        'write_to_template': "__version__ = '{version}'\n"}


if __name__ == "__main__":
    setup(
        use_scm_version=_getversion,
    )
