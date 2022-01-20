# python-library-mockup
JUelich NeuroImaging FEature extractoR

## Repository Organization

* `docs`: Documentation, built using sphinx.
* `examples`: Examples, using sphinx-gallery. File names of examples that create visual output must start with `plot_`, otherwise, with `run_`.
* `junifer`: Main library directory
  * `api`: User API module
  * `data`: Module that handles data required for the library to work (e.g. atlases)
  * `datagrabber`: DataGrabber module.
  * `datareader`: DataReader module.
  * `markers`: Markers module.
  * `pipeline`: Pipeline module.
  * `preprocess`: Preprocessing module.
  * `storage`: Storage module.
  * `utils`: Utilities module (e.g. logging)
  

  