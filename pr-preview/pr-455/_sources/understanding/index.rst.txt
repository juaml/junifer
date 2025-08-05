.. include:: ../links.inc

.. _understanding:

Understanding ``junifer``
=========================

Before you start, you should understand how ``junifer`` works. ``junifer`` is a
tool conceived to extract features from neuroimaging data in an easy-to-use
manner, with minimal coding and minimal user expertise in the internal aspects.

Unlike other tools like FSL, SPM, AFNI, etc., ``junifer`` is not a toolbox to
pre-process data, but a toolbox to extract features from previously
pre-processed data.

The main idea is that you have a set of images (e.g. a set of functional MRI,
structural MRI, diffusion MRI, etc.) and you want to extract features to
later use in statistical analyses or machine learning (for example, using
julearn_).

.. important::

   ``junifer`` is not a toolbox to create pipelines, but a tool to configure the
   ``junifer`` pipeline, which is intended to be fixed and not to be changed. If
   you want to create a pipeline, you should use other tools like nipype_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   pipeline
   data
   datagrabber
   datareader
   preprocess
   marker
   storage
