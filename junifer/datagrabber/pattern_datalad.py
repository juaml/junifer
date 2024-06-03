"""Provide concrete implementation for pattern + datalad based DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from ..api.decorators import register_datagrabber
from ..utils import logger
from .datalad_base import DataladDataGrabber
from .pattern import PatternDataGrabber


__all__ = ["PatternDataladDataGrabber"]


@register_datagrabber
class PatternDataladDataGrabber(DataladDataGrabber, PatternDataGrabber):
    """Concrete implementation for pattern and datalad based data fetching.

    Implements a DataGrabber that gets data from a datalad sibling,
    interpreting patterns.

    Parameters
    ----------
    types : list of str
        The types of data to be grabbed.
    patterns : dict
        Data type patterns as a dictionary. It has the following schema:

        * ``"T1w"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": {
                  "mask": {
                      "mandatory": ["pattern", "space"],
                      "optional": []
                  }
              }
            }

        * ``"T2w"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": {
                  "mask": {
                      "mandatory": ["pattern", "space"],
                      "optional": []
                  }
              }
            }

        * ``"BOLD"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": {
                  "mask": {
                      "mandatory": ["pattern", "space"],
                      "optional": []
                  }
                  "confounds": {
                      "mandatory": ["pattern", "format"],
                      "optional": []
                  }
              }
            }

        * ``"Warp"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "src", "dst"],
              "optional": []
            }

        * ``"VBM_GM"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": []
            }

        * ``"VBM_WM"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": []
            }

        Basically, for each data type, one needs to provide ``mandatory`` keys
        and can choose to also provide ``optional`` keys. The value for each
        key is a string. So, one needs to provide necessary data types as a
        dictionary, for example:

        .. code-block:: none

          {
              "BOLD": {
                "pattern": "...",
                "space": "...",
              },
              "T1w": {
                "pattern": "...",
                "space": "...",
              },
              "Warp": {
                "pattern": "...",
                "src": "...",
                "dst": "...",
              }
          }

        taken from :class:`.HCP1200`.
    replacements : str or list of str
        Replacements in the ``pattern`` key of each data type. The value needs
        to be a list of all possible replacements.
    confounds_format : {"fmriprep", "adhoc"} or None, optional
        The format of the confounds for the dataset (default None).
    datadir : str or pathlib.Path or None, optional
        That directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    rootdir : str or pathlib.Path, optional
        The path within the datalad dataset to the root directory
        (default ".").
    uri : str or None, optional
        URI of the datalad sibling (default None).

    See Also
    --------
    DataladDataGrabber:
        Abstract base class for datalad-based data fetching.
    PatternDataGrabber:
        Concrete implementation for pattern-based data fetching.

    """

    def __init__(
        self,
        **kwargs,
    ) -> None:
        # TODO(synchon): needs to be reworked, DataladDataGrabber needs to be
        # a mixin to avoid multiple inheritance wherever possible.

        logger.debug("Initializing PatternDataladDataGrabber")
        for key, val in kwargs.items():
            logger.debug(f"\t{key} = {val}")

        super().__init__(**kwargs)
