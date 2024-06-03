.. include:: ../links.inc

.. _data_object:

The Data Object
===============

Description
-----------

This is the *object* that traverses the steps of the pipeline. It is indeed a
dictionary of dictionaries. The first level of keys are the :ref:`data types <data_types>`
and the values are the corresponding information as dictionaries.

.. code-block::

   {'BOLD': {...}, 'T1w': {...}}

The second level of keys are the actual data. A special second-level key named
``meta`` is present in each step, that contains all the information on the
data type including source and previous transformation steps.

The :ref:`Data Grabber <datagrabber>` step adds the ``path`` second-level key
which gives the path to the file containing the data. The ``meta`` key in this
step only contains information about the DataGrabber used.

.. code-block::

   {'BOLD': {'meta': {'datagrabber': {'class': 'SPMAuditoryTestingDataGrabber',
                                      'types': ['BOLD', 'T1w']},
                      'dependencies': set(),
                      'element': {'subject': 'sub001'}},
             'path': PosixPath('/var/folders/dv/2lbr8f8j0q12zrx3mz3ll5m40000gp/T/tmpgxcyjfo1/sub001_bold.nii.gz')},
    'T1w': {'meta': {'datagrabber': {'class': 'SPMAuditoryTestingDataGrabber',
                                     'types': ['BOLD', 'T1w']},
                     'dependencies': set(),
                     'element': {'subject': 'sub001'}},
            'path': PosixPath('/var/folders/dv/2lbr8f8j0q12zrx3mz3ll5m40000gp/T/tmpgxcyjfo1/sub001_T1w.nii.gz')}}

The :ref:`Data Reader <datareader>` step adds the ``data`` second-level key
which is the actual data loaded into memory. The ``meta`` key in this step
adds information about the DataReader used to read the data.

.. code-block::

   {'BOLD': {'data': <nibabel.nifti1.Nifti1Image object at 0x16b5d8910>,
             'meta': {'datagrabber': {'class': 'SPMAuditoryTestingDataGrabber',
                                      'types': ['BOLD', 'T1w']},
                      'datareader': {'class': 'DefaultDataReader'},
                      'dependencies': {'nilearn'},
                      'element': {'subject': 'sub001'}},
             'path': PosixPath('/var/folders/dv/2lbr8f8j0q12zrx3mz3ll5m40000gp/T/tmpe49321ce/sub001_bold.nii.gz')},
    'T1w': {'data': <nibabel.nifti1.Nifti1Image object at 0x16b5d78d0>,
            'meta': {'datagrabber': {'class': 'SPMAuditoryTestingDataGrabber',
                                     'types': ['BOLD', 'T1w']},
                     'datareader': {'class': 'DefaultDataReader'},
                     'dependencies': set(),
                     'element': {'subject': 'sub001'}},
            'path': PosixPath('/var/folders/dv/2lbr8f8j0q12zrx3mz3ll5m40000gp/T/tmpe49321ce/sub001_T1w.nii.gz')}}


The :ref:`Preprocess <preprocess>` step, if used, modifies the ``data``
second-level key's value and appends the ``meta`` key with information about
the preprocessor.

The :ref:`Marker <marker>` step removes the ``path`` second-level key,
replaces the ``data`` second-level key's value with the marker's computed value
and adds further keys needed for the storage, for example, ``col_names``.

.. code-block::

   {'BOLD': {'col_names': ['root_sum_of_squares_ets'],
             'data': ...,
             'meta': {'datagrabber': {'class': 'SPMAuditoryTestingDataGrabber',
                                      'types': ['BOLD', 'T1w']},
                      'datareader': {'class': 'DefaultDataReader'},
                      'dependencies': {'nilearn'},
                      'element': {'subject': 'sub001'},
                      'marker': {'agg_method': 'mean',
                                 'agg_method_params': None,
                                 'class': 'RSSETSMarker',
                                 'masks': None,
                                 'name': 'RSSETSMarker',
                                 'parcellation': 'Schaefer100x17'},
                      'type': 'BOLD'}}}

.. note::

   You never directly interact with the *data object* but it's important to know
   where and how the object is being manipulated to reason about your pipeline.

.. _data_types:

Data Types
----------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Description
     - Example
   * - ``T1w``
     - T1w image (3D)
     - Preprocessed or Raw T1w image
   * - ``T2w``
     - T2w image (3D)
     - Preprocessed or Raw T2w image
   * - ``BOLD``
     - BOLD image (4D)
     - Preprocessed or Denoised BOLD image (fMRIPrep output)
   * - ``VBM_GM``
     - VBM Gray Matter segmentation (3D)
     - CAT output (`m0wp1` images)
   * - ``VBM_WM``
     - VBM White Matter segmentation (3D)
     - CAT output (`m0wp2` images)
   * - ``VBM_CSF``
     - VBM Central Spinal Fluid segmentation (3D)
     - CAT output (`m0wp3` images)
   * - ``fALFF``
     - Voxel-wise fALFF image (3D)
     - fALFF computed with CONN toolbox
   * - ``GCOR``
     - Global Correlation image (3D)
     - GCOR computed with CONN toolbox
   * - ``LCOR``
     - Local Correlation image (3D)
     - LCOR computed with CONN toolbox
   * - ``DWI``
     - Diffusion-weighted image (3D)
     - Diffusion-weighted image (FSL or MRtrix output)
   * - ``FreeSurfer``
     - T1 image (3D)
     - T1 image computed by FreeSurfer
