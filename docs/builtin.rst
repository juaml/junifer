.. include:: links.inc

Pipeline steps and atlases
==========================


Data Grabbers
^^^^^^^^^^^^^

..
    Provide a list of the DataGrabbers that are implemented or planned.
    Access: Valid options are
        - Open
        - Open with registration
        - Restricted

    Type/config: this should mention weather the class is built-in in the
    core of junifer or needs to be imported from a specific configuration in
    the `junifer.configs` module.

    State: this should indicate the state of the dataset. Valid options are
    - Planned
    - In Progress
    - Done

    Version added: If the status is "Done", the Junifer version in which the
    dataset was added. Else, a link to the Github issue or pull request
    implementing the dataset. Links to github can be added by using the
    following syntax: :gh:`<issue number>`

Available
---------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Class
     - Description
     - Access
     - Type/Config
     - State
     - Version Added
   * - :class:`junifer.datagrabber.DataladHCP1200`
     - `HCP OpenAccess dataset <https://github.com/datalad-datasets/human-connectome-project-openaccess>`_
     - Open with registration
     - Built-in
     - In Progress
     - :gh:`4`
   * - :class:`junifer.configs.juseless.JuselessDataladUKBVBM`
     - UKB VBM dataset preprocessed with CAT. Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1
   * - :class:`junifer.configs.juseless.datagrabbers.JuselessDataladCamCANVBM`
     - CamCAN VBM dataset preprocessed with CAT. Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless.datagrabbers``
     - Done
     - 0.0.1
   * - :class:`junifer.datagrabber.DataladAOMICID1000`
     - `AOMIC 1000 dataset <https://github.com/OpenNeuroDatasets/ds003097>`_
     - Open without registration
     - Built-in
     - Done
     - 0.0.1
   * - :class:`junifer.datagrabber.DataladAOMICPIOP1`
     - `AOMIC PIOP1 dataset <https://github.com/OpenNeuroDatasets/ds002785>`_
     - Open without registration
     - Built-in
     - Done
     - 0.0.1
   * - :class:`junifer.datagrabber.DataladAOMICPIOP2`
     - `AOMIC PIOP2 dataset <https://github.com/OpenNeuroDatasets/ds002790>`_
     - Open without registration
     - Built-in
     - Done
     - 0.0.1
   * - :class:`junifer.configs.juseless.JuselessDataladAOMICVBM`
     - AOMIC VBM dataset. Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - In Progress
     - :gh:`57`


Planned
-------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Description
     - Access
     - Type/Config
     - Reference
   * - ENKI
     - ENKI dataset for Juseless
     - Restricted
     - ``junifer.configs.juseless``
     - :gh:`47`
   * - IXI
     - IXI dataset for Juseless
     - Restricted
     - ``junifer.configs.juseless``
     - :gh:`48`
   * - UCLA
     - UCLA dataset for Juseless
     - Built-in
     - ``junifer.configs.juseless``
     - :gh:`88`


Markers
^^^^^^^

..
    Provide a list of the Markers that are implemented or planned.

    State: this should indicate the state of the dataset. Valid options are
    - Planned
    - In Progress
    - Done

    Version added: If the status is "Done", the Junifer version in which the
    dataset was added. Else, a link to the Github issue or pull request
    implementing the dataset. Links to github can be added by using the
    following syntax: :gh:`<issue number>`

Available
---------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Class
     - Description
     - State
     - Version Added
   * - :class:`junifer.markers.ParcelAggregation`
     - Apply parcellation and perform aggregation function
     - Done
     - 0.0.1
   * - :class:`junifer.markers.FunctionalConnectivityAtlas`
     - Compute functional connectivity
     - Done
     - 0.0.1
   * - :class:`junifer.markers.SphereAggregation`
     - Spherical aggregation using mean
     - Done
     - 0.0.1
   * - :class:`junifer.markers.RSSETSMarker`
     - Compute root sum of squares of edgewise timeseries
     - Done
     - 0.0.1


Planned
-------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Description
     - Reference
   * - Connectedness
     - Compute connectedness
     - :gh:`34`
   * - ALFF and (f)ALFF
     - Detect amplitude of low-frequency fluctuation (ALFF) for resting-state fMRI
     - :gh:`35`
   * - ReHo
     - Calculate regional homogeneity
     - :gh:`36`
   * - Permutation entropy, Range entropy, Multiscale entropy and Hurst exponent
     - Calculate Permutation entropy, Range entropy, Multiscale entropy and Hurst exponent
     - :gh:`61`
   * - EdgeCentricFC
     - Calculate edge-centric functional connectivity
     - :gh:`64`
   * - CrossAtlasFC
     - Calculate cross-atlas functional connectivity
     - :gh:`85`


Atlases
^^^^^^^

Available
---------

========  =================  =================================================================================  =============  ====================================================
Name      Options            Keys                                                                               Version added  Publication
========  =================  =================================================================================  =============  ====================================================
Schaefer  ``n_rois``,        | ``Schaefer900x7``, ``Schaefer1000x7``, ``Schaefer100x17``, ``Schaefer200x17``,   0.0.1          | Alexander Schaefer, Ru Kong, Evan M Gordon,
          ``yeo_networks``   | ``Schaefer300x17``, ``Schaefer400x17``, ``Schaefer500x17``, ``Schaefer600x17``,                 | Timothy O Laumann, Xi-Nian Zuo, Avram J Holmes,
                             | ``Schaefer700x17``, ``Schaefer800x17``, ``Schaefer900x17``, ``Schaefer1000x17``                 | Simon B Eickhoff, B T Thomas Yeo. Local-Global
                                                                                                                               | Parcellation of the Human Cerebral Cortex from
                                                                                                                               | Intrinsic Functional Connectivity MRI, Cerebral
                                                                                                                               | Cortex, Volume 28, Issue 9, September 2018, Pages
                                                                                                                               | 3095–3114.
                                                                                                                               | https://doi.org/10.1093/cercor/bhx179
SUIT      ``space``          | ``SUITxMNI``, ``SUITxSUIT``                                                      0.0.1          | Diedrichsen J. (2006). A spatially unbiased atlas
                                                                                                                               | template of the human cerebellum. NeuroImage,
                                                                                                                               | 33(1), 127–138.
                                                                                                                               | https://doi.org/10.1016/j.neuroimage.2006.05.056
TIAN      ``scale``,         | ``TianxS1x3TxMNI6thgeneration``, ``TianxS1x3TxMNInonlinear2009cAsym``,           0.0.1          | Tian, Y., Margulies, D.S., Breakspear, M. et al.
          ``space``,         | ``TianxS1x7TxMNI6thgeneration``, ``TianxS2x3TxMNI6thgeneration``,                               | Topographic organization of the human subcortex
          ``magneticfield``  | ``TianxS2x3TxMNInonlinear2009cAsym``, ``TianxS2x7TxMNI6thgeneration``,                          | unveiled with functional connectivity gradients.
                             | ``TianxS3x3TxMNI6thgeneration``, ``TianxS3x3TxMNInonlinear2009cAsym``,                          | Nat Neurosci 23, 1421–1432 (2020).
                             | ``TianxS3x7TxMNI6thgeneration``, ``TianxS4x3TxMNI6thgeneration``,                               | https://doi.org/10.1038/s41593-020-00711-6
                             | ``TianxS4x3TxMNInonlinear2009cAsym``, ``TianxS4x7TxMNI6thgeneration``
========  =================  =================================================================================  =============  ====================================================


Planned
-------

=================  ==============================================================================
Name               Publication
=================  ==============================================================================
Desikan-Killiany   | Desikan, R. S., Ségonne, F., Fischl, B., Quinn, B. T., Dickerson, B. C.,
                   | Blacker, D., et al. (2006). An automated labeling system for
                   | subdividing the human cerebral cortex on MRI scans into gyral based
                   | regions of interest. NeuroImage, 31(3), 968-980.
                   | http://doi.org/10.1016/j.neuroimage.2006.01.021
Glasser            | Glasser, M. F., Coalson, T. S., Robinson, E. C., Hacker, C. D.,
                   | Harwell, J., Yacoub, E., et al. (2016). A multi-modal  parcellation
                   | of human cerebral cortex. Nature.
                   | http://doi.org/10.1038/nature18933
AAL                | Rolls, E. T., Huang, C. C., Lin, C. P., Feng, J., & Joliot, M. (2020).
                   | Automated anatomical labelling atlas 3. Neuroimage, 206, 116189.
                   | https://doi.org/10.1016/j.neuroimage.2019.116189
Shen               | Shen X, Tokoglu F, Papademetris X, Constable RT. Groupwise whole-brain
                   | parcellation from resting-state fMRI data for network node identification.
                   | Neuroimage. 2013 Nov 15;82:403-15.
                   | https://doi.org/10.1016/j.neuroimage.2013.05.081.
Mindboggle 101     | Klein, A., & Tourville, J. (2012). 101 labeled brain images and a
                   | consistent human cortical labeling protocol. Frontiers in Neuroscience.
                   | http://doi.org/10.3389/fnins.2012.00171/abstract
Destrieux          | Destrieux, C., Fischl, B., Dale, A., & Halgren, E. (2010). Automatic
                   | parcellation of human cortical gyri and sulci using standard anatomical
                   | nomenclature. NeuroImage, 53(1), 1–15.
                   | http://doi.org/10.1016/j.neuroimage.2010.06.010.
Fan                | Fan, L., Li, H., Zhuo, J., Zhang, Y., Wang, J., Chen, L., ...
                   | & Jiang, T. (2016). The human brainnetome atlas: a new brain atlas based
                   | on connectional architecture. Cerebral cortex, 26(8), 3508-3526.
                   | https://doi.org/10.1093/cercor/bhw157
Buckner            | Buckner, R. L., Krienen, F. M., Castellanos, A., Diaz, J. C.,
                   | & Yeo, B. T. T. (2011). The organization of the human cerebellum
                   | estimated by intrinsic functional connectivity. Journal of Neurophysiology,
                   | 106(5), 2322–2345.
                   | https://doi.org/10.1152/jn.00339.2011
                   | Yeo, B. T. T., Krienen, F. M., Sepulcre, J., Sabuncu, M. R., Lashkari, D.,
                   | Hollinshead, M., et al. (2011). The organization of the human cerebral
                   | cortex estimated by intrinsic functional connectivity.
                   | Journal of Neurophysiology, 106(3), 1125–1165.
                   | https://doi.org/10.1152/jn.00338.2011
=================  ==============================================================================

..
  helpful site for creating tables: https://rest-sphinx-memo.readthedocs.io/en/latest/ReST.html#tables
