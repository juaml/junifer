.. include:: ../links.inc

.. _marker:

Marker
======

Description
-----------

The ``Marker`` is an object that is responsible for feature extraction. It primarily operates on data loaded
in memory by :ref:`Data Reader <datareader>` and stored in the ``data`` key of each :ref:`data type <data_types>`
in the :ref:`Data object <data_object>`. In some cases, it can also operate on pre-processed data as obtained
from the :ref:`Preprocess <preprocess>` step of the pipeline. It is important to note that this pre-process is
not similar to pre-processing done by tools like FSL, SPM, AFNI, etc. . For example, one can perform confound
removal on loaded data and then perform feature extraction.

Markers are meant to be used inside the datagrabber context but you can operate on them outside the context as long
as the actual data is in the memory and the Python runtime has not garbage-collected it.

If you are interested in using already provided markers, please go to :doc:`../builtin`. And, if you want to implement
your own marker, you need to provide concrete implementation of :class:`junifer.markers.BaseMarker`. Specifically, you
need to override ``get_output_type``, ``store`` and ``compute`` methods.
