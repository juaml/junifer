# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
# License: AGPL
from importlib_metadata import version
import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()


def _getversion():
    from setuptools_scm.version import get_local_node_and_date, \
        simplified_semver_version

    def clean_scheme(version):
        print(version)
        return get_local_node_and_date(version) if version.dirty else ""

    return {
        'version_scheme': simplified_semver_version,
        'local_scheme': clean_scheme,
        'write_to': 'junifer/_version.py',
        'write_to_template': "__version__ = '{version}'\n"}


DOWNLOAD_URL = 'https://github.com/juaml/junifer'
URL = 'https://juaml.github.io/junifer'

setuptools.setup(
    name='junifer',
    author='Fede Raimondo',
    author_email='f.raimondo@fz-juelich.de',
    description='JUelich NeuroImaging FEature extractoR',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=URL,
    download_url=DOWNLOAD_URL,
    packages=setuptools.find_packages(),
    zip_safe=False,
    classifiers=['Intended Audience :: Science/Research',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved',
                 'Programming Language :: Python',
                 'Topic :: Software Development',
                 'Topic :: Scientific/Engineering',
                 'Operating System :: Microsoft :: Windows',
                 'Operating System :: POSIX',
                 'Operating System :: Unix',
                 'Operating System :: MacOS',
                 'Programming Language :: Python :: 3'],
    project_urls={
        'Documentation': URL,
        'Source': DOWNLOAD_URL,
        'Tracker': f'{DOWNLOAD_URL}issues/',
    },
    install_requires=[],  # TODO: Complete
    python_requires='>=3.6',
    use_scm_version=_getversion,
    setup_requires=['setuptools_scm'],
)
