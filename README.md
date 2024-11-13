![Junifer logo](docs/images/junifer_logo.png "junifer logo")

# junifer - JUelich NeuroImaging FEature extractoR

![PyPI](https://img.shields.io/pypi/v/junifer?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/junifer?style=flat-square)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/junifer?style=flat-square)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/junifer/badges/version.svg)](https://anaconda.org/conda-forge/junifer)
![GitHub](https://img.shields.io/github/license/juaml/junifer?style=flat-square)
![Codecov](https://img.shields.io/codecov/c/github/juaml/junifer?style=flat-square)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8176570.svg)](https://doi.org/10.5281/zenodo.8176570)
[![FAIR checklist badge](https://fairsoftwarechecklist.net/badge.svg)](https://fairsoftwarechecklist.net/v0.2?f=31&a=32113&i=32322&r=133)

## About

`junifer` is a data handling and feature extraction library targeted towards neuroimaging data specifically functional MRI data.

It is currently being developed and maintained at the [Applied Machine Learning](https://www.fz-juelich.de/en/inm/inm-7/research-groups/applied-machine-learning-aml) group at [Forschungszentrum Juelich](https://www.fz-juelich.de/en), Germany. Although the library is designed for people working at [Institute of Neuroscience and Medicine - Brain and Behaviour (INM-7)](https://www.fz-juelich.de/en/inm/inm-7), it is designed to be as modular as possible thus enabling others to extend it easily.

The documentation is available at [https://juaml.github.io/junifer](https://juaml.github.io/junifer/main/index.html).

## Repository Organization

* `docs`: Documentation, built using sphinx.
* `examples`: Examples, using sphinx-gallery. File names of examples that create visual output must start with `plot_`, otherwise, with `run_`.
* `junifer`: Main library directory.
  * `api`: User API module.
  * `configs`: Module for pre-defined configs for most used computing clusters.
  * `data`: Module that handles data required for the library to work (e.g. parcels, coordinates).
  * `datagrabber`: DataGrabber module.
  * `datareader`: DataReader module.
  * `external`: Module for external libraries and tools.
  * `markers`: Markers module.
  * `onthefly`: Transformation components (on-the-fly) module.
  * `pipeline`: Pipeline module.
  * `preprocess`: Preprocessing module.
  * `storage`: Storage module.
  * `testing`: Testing components module.
  * `typing`: Type hints module.
  * `utils`: Utilities module (e.g. logging).

## Installation

Use `pip` to install from PyPI like so:

```
pip install junifer
```

You can also install via `conda`, like so:

```
conda install -c conda-forge junifer
```

### Optional dependencies

`junifer` supports a few optional dependencies to enable certain features. You can
install them by specifying a comma separated list within square brackets, like so:

```
pip install "junifer[bct,dev]"
```

* `bct` installs [bctpy](https://github.com/aestrivex/bctpy) to enable use of `onthefly` module.
* `neurokit2` installs [neurokit2](https://github.com/neuropsychology/NeuroKit) to enable use of [complexity markers](https://juaml.github.io/junifer/main/api/markers.html#module-junifer.markers.complexity).
* `all` includes all of the above.
* `dev` installs packages needed for development.
* `docs` installs packages needed for building documentation.

## Citation

If you use `junifer` in a scientific publication, we would appreciate if you cite our work. Currently, we do not have a publication, so feel free to use the project's [Zenodo URL](https://doi.org/10.5281/zenodo.8176569).

## Funding

We thank the [Helmholtz Imaging Platform](https://helmholtz-imaging.de/) and
[SMHB](https://www.fz-juelich.de/en/smhb) for supporting development of `junifer`.
(The funding sources had no role in the design, implementation and evaluation of the pipeline.)

## Contribution

Contributions are welcome and greatly appreciated. Please read the [guidelines](https://juaml.github.io/junifer/main/contributing.html) to get started.

## License

junifer is released under the AGPL v3 license:

junifer, FZJuelich AML neuroimaging feature extraction library.
Copyright (C) 2023, authors of junifer.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
