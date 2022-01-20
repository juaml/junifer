# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
# License: AGPL
import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()


DOWNLOAD_URL = '<GITHUB_URL>'
URL = '<DOC_URL>'

setuptools.setup(
    name='<PKG_NAME>',
    author='<AUTHOR_NAME>',
    author_email='<AUTHOR_EMAIL>',
    description='<SHORT_DESC>',
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
    use_scm_version=dict(
        version_scheme="python-simplified-semver",
        local_scheme="node-and-date",
        write_to="<PKG_NAME>/_version.py",
        write_to_template="__version__ = '{version}'\n"
    ),
    setup_requires=['setuptools_scm'],
)
