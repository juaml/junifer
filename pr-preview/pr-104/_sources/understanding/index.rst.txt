.. include:: ../links.inc

.. _understanding:

Understanding junifer
=====================

Before you start, you should understand how junifer works. Junifer is a
tool conceived to extract features from neuroimaging data in a easy-to-use
manner, with minimal coding and minimal user expertise in the internal aspects.

Unlike other tools like FSL, SPM, AFNI, etc., junifer is not a toolbox to
pre-process data, but a toolbox to extract features from previously pre-processed
data.

The main idea is that you have a set of images (e.g. a set of functional MRI,
structural MRI, diffusion MRI, etc.) and you want to extract features to
later use in stastical analyses or machine learning (for example, using
julearn_).


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   data
   datagrabber
   datareader
   marker
   storage
