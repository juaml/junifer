.. include:: ../links.inc

.. _pipeline:

The ``junifer`` Pipeline
========================

The junifer pipeline is the main execution path of junifer. It consists of five
steps:

1. :ref:`Data Grabber <datagrabber>`: Interpret the dataset and provide a list
   of files.
2. :ref:`Data Reader <datareader>`: Read the files.
3. :ref:`Preprocess <preprocess>`: Prepare the files' data for marker
   computation.
4. :ref:`Marker Computation <marker>`: Compute the marker(s).
5. :ref:`Storage <storage>`: Store the marker(s) values.

The element that is passed across the pipeline is called the
:ref:`Data Object<data_object>`.

The following is a graphical representation of the pipeline:

.. mermaid::

   flowchart LR
     dg[Data Grabber]
     dr[Data Reader]
     pp[Preprocess]
     mc[Marker Computation]
     st[Storage]
     dg --> dr
     dr --> pp
     pp --> mc
     mc --> st


However, it is usually the case that several markers are computed for the same
data. Thus, the ``Marker Computation`` step of the pipeline is defined as a list
of markers. The following is a graphical representation of the pipeline execution
on multiple markers:

.. mermaid::

   flowchart LR
     dg[Data Grabber]
     dr[Data Reader]
     pp[Preprocess]
     mc1[Marker Computation]
     mc2[Marker Computation]
     mc3[Marker Computation]
     mc4[Marker Computation]
     mc5[Marker Computation]
     st1[Storage]
     st2[Storage]
     st3[Storage]
     st4[Storage]
     st5[Storage]
     dg --> dr
     dr --> pp
     pp --> mc1
     pp --> mc2
     pp --> mc3
     pp --> mc4
     pp --> mc5
     mc1 --> st1
     mc2 --> st2
     mc3 --> st3
     mc4 --> st4
     mc5 --> st5

.. note::

   To avoid keeping in memory all of the computed marker, the storage step is
   called after each marker computation, releasing the memory used to compute
   each marker.
