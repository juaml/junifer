"""Provide concrete implementation for pattern + datalad based DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from fnmatch import fnmatchcase
from pathlib import Path

from pydantic import ConfigDict

from ..api.decorators import register_datagrabber
from ..utils import raise_error
from .base import logger
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
    uri : pydantic.AnyUrl
        URI of the datalad sibling.
    types : enum:`.DataType` or list of variants
        The data type(s) to grab.
    patterns : ``DataGrabberPatterns``
        The datagrabber patterns. Check :class:`DataTypeSchema` for the schema.
    replacements : list of str
        All possible replacements in ``patterns.<data_type>.pattern``.
    rootdir : pathlib.Path, optional
        The path within the datalad dataset to the root directory
        (default Path(".")).
    confounds_format : :enum:`.ConfoundsFormat` or None, optional
        The format of the confounds for the dataset (default None).
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.


    See Also
    --------
    DataladDataGrabber:
        Abstract base class for datalad-based data fetching.
    PatternDataGrabber:
        Concrete implementation for pattern-based data fetching.

    """

    model_config = ConfigDict(extra="allow")

    def validate_datagrabber_params(self) -> None:
        """Run extra logical validation for datagrabber."""
        super().validate_datagrabber_params()
        logger.debug("Initializing PatternDataladDataGrabber")
        for key, val in self.__pydantic_extra__.items():
            logger.debug(f"\t{key} = {val}")

    def install(self) -> None:
        """Install the datalad dataset and check the patterns.

        The elements are found by searching the files of the patterns, but the
        files of a sub-dataset are only there once the sub-dataset is
        installed, so the patterns cannot search the files of the
        sub-datasets (e.g., with one sub-dataset per subject).

        Raises
        ------
        RuntimeError
            If a pattern searches the files of a sub-dataset.

        """
        super().install()
        subdatasets = [
            Path(x)
            for x in self._dataset.subdatasets(
                result_xfm="relpaths",
                result_renderer="disabled",
                return_type="list",
            )
        ]
        if len(subdatasets) == 0:
            return
        for data_type in self.types:
            for pattern in self._get_type_patterns(data_type):
                _, glob_pattern, _ = self._replace_patterns_regex(pattern)
                if not any(x in glob_pattern for x in "*?["):
                    continue
                pattern_parts = (self.rootdir / glob_pattern).parts
                for subdataset in subdatasets:
                    n_parts = len(subdataset.parts)
                    if len(pattern_parts) > n_parts and all(
                        fnmatchcase(x, y)
                        for x, y in zip(
                            subdataset.parts, pattern_parts, strict=False
                        )
                    ):
                        # Remove the dataset if cloned, as the context is
                        # not entered
                        self.cleanup()
                        raise_error(
                            msg=(
                                f"The pattern {pattern} of {data_type} "
                                "searches the files of the sub-dataset "
                                f"{subdataset}, which are only there if it "
                                "is installed. A DataGrabber with files in "
                                "sub-datasets must list its elements and "
                                "build the paths of the files without "
                                "searching them (e.g., without wildcards), "
                                "as DataladHCP1200."
                            ),
                            klass=RuntimeError,
                        )
