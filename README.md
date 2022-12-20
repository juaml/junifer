![Junifer logo](docs/images/junifer_logo.png "junifer logo")

# junifer - JUelich NeuroImaging FEature extractoR

![PyPI](https://img.shields.io/pypi/v/junifer?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/junifer?style=flat-square)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/junifer?style=flat-square)
![GitHub](https://img.shields.io/github/license/juaml/junifer?style=flat-square)
![Codecov](https://img.shields.io/codecov/c/github/juaml/junifer?style=flat-square)

## About

junifer is a data handling and feature extraction library targeted towards neuroimaging data specifically functional MRI data.

It is curently being developed and maintained at the [Applied Machine Learning](https://www.fz-juelich.de/en/inm/inm-7/research-groups/applied-machine-learning-aml) group at [Forschungszentrum Juelich](https://www.fz-juelich.de/en), Germany. Although the library is designed for people working at [Institute of Neuroscience and Medicine - Brain and Behaviour (INM-7)](https://www.fz-juelich.de/en/inm/inm-7), it is designed to be as modular as possible thus enabling others to extend it easily.

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
  * `markers`: Markers module.
  * `pipeline`: Pipeline module.
  * `preprocess`: Preprocessing module.
  * `storage`: Storage module.
  * `testing`: Testing components module.
  * `utils`: Utilities module (e.g. logging)


## Installation

Use `pip` to install from PyPI like so:

```
pip install junifer
```

## Citation

If you use junifer in a scientific publication, we would appreciate if you cite our work. Currently, we do not have a publication, so feel free to use the project [URL](https://juaml.github.io/junifer).

## Funding

We thank the [Helmholtz Imaging Platform](https://helmholtz-imaging.de/) and
[SMHB](https://www.fz-juelich.de/en/smhb) for supporting development of Junifer.
(The funding sources had no role in the design, implementation and evaluation of the pipeline.)

## Contribution

Contributions are welcome and greatly appreciated. Please read the [guidelines](https://juaml.github.io/junifer/main/contributing.html) to get started.

## License

junifer is released under the AGPL v3 license:

junifer, FZJuelich AML neuroimaging feature extraction library.
Copyright (C) 2022, authors of junifer.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
