.. include:: links.inc

Built-in Pipeline steps and data
================================


Data Grabbers
-------------

..
    Provide a list of the DataGrabbers that are implemented or planned.
    Access: Valid options are
        - Open
        - Open with registration
        - Restricted

    Type/config: this should mention whether the class is built-in in the
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
~~~~~~~~~

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
     - Done
     - 0.0.1
   * - :class:`junifer.configs.juseless.datagrabbers.JuselessDataladUKBVBM`
     - UKB VBM dataset preprocessed with CAT. Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1
   * - :class:`junifer.configs.juseless.datagrabbers.JuselessDataladCamCANVBM`
     - CamCAN VBM dataset preprocessed with CAT. Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
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
   * - :class:`junifer.configs.juseless.datagrabbers.JuselessDataladAOMICID1000VBM`
     - AOMIC ID1000 VBM dataset. Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1
   * - :class:`junifer.configs.juseless.datagrabbers.JuselessDataladIXIVBM`
     - `IXI VBM dataset <https://brain-development.org/ixi-dataset/>`_. Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1
   * - :class:`junifer.configs.juseless.datagrabbers.JuselessUCLA`
     - UCLA fMRIPrep dataset. Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1

Planned
~~~~~~~

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


Markers
-------

..
    Provide a list of the Markers that are implemented or planned.

    State: this should indicate the state of the marker. Valid options are
    - Planned
    - In Progress
    - Done

    Version added: If the status is "Done", the Junifer version in which the
    marker was added. Else, a link to the Github issue or pull request
    implementing the marker. Links to github can be added by using the
    following syntax: :gh:`<issue number>`

Available
~~~~~~~~~

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
   * - :class:`junifer.markers.FunctionalConnectivityParcels`
     - Compute functional connectivity over parcellation
     - Done
     - 0.0.1
   * - :class:`junifer.markers.CrossParcellationFC`
     - Compute functional connectivity across two parcellations
     - Done
     - 0.0.1
   * - :class:`junifer.markers.SphereAggregation`
     - Spherical aggregation using mean
     - Done
     - 0.0.1
   * - :class:`junifer.markers.FunctionalConnectivitySpheres`
     - Compute functional connectivity over spheres placed on coordinates
     - Done
     - 0.0.1
   * - :class:`junifer.markers.RSSETSMarker`
     - Compute root sum of squares of edgewise timeseries
     - Done
     - 0.0.1


Planned
~~~~~~~

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


Parcellations
-------------

..
    Provide a list of the Parcellations that are implemented or planned.

    Version added: The Junifer version in which the parcellation was added.

Available
~~~~~~~~~

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Options
     - Keys
     - Version added
     - Publication
   * - Schaefer
     - ``n_rois``, ``yeo_networks``
     - | ``Schaefer900x7``, ``Schaefer1000x7``, ``Schaefer100x17``,
       | ``Schaefer200x17``, ``Schaefer300x17``, ``Schaefer400x17``,
       | ``Schaefer500x17``, ``Schaefer600x17``, ``Schaefer700x17``,
       | ``Schaefer800x17``, ``Schaefer900x17``, ``Schaefer1000x17``
     - 0.0.1
     - | Schaefer, A., Kong, R., Gordon, E.M. et al.
       | Local-Global Parcellation of the Human Cerebral Cortex from
       | Intrinsic Functional Connectivity MRI
       | Cerebral Cortex, Volume 28(9), Pages 3095–3114 (2018).
       | https://doi.org/10.1093/cercor/bhx179
   * - SUIT
     - ``space``
     - ``SUITxMNI``, ``SUITxSUIT``
     - 0.0.1
     - | Diedrichsen, J.
       | A spatially unbiased atlas template of the human cerebellum.
       | NeuroImage, Volume 33(1), Pages 127–138 (2006).
       | https://doi.org/10.1016/j.neuroimage.2006.05.056
   * - TIAN
     - ``scale``, ``space``, ``magneticfield``
     - | ``TianxS1x3TxMNI6thgeneration``, ``TianxS1x7TxMNI6thgeneration``,
       | ``TianxS2x3TxMNI6thgeneration``, ``TianxS2x7TxMNI6thgeneration``,
       | ``TianxS3x3TxMNI6thgeneration``, ``TianxS3x7TxMNI6thgeneration``,
       | ``TianxS4x3TxMNI6thgeneration``, ``TianxS4x7TxMNI6thgeneration``,
       | ``TianxS1x3TxMNInonlinear2009cAsym``, ``TianxS2x3TxMNInonlinear2009cAsym``,
       | ``TianxS3x3TxMNInonlinear2009cAsym``, ``TianxS4x3TxMNInonlinear2009cAsym``
     - 0.0.1
     - | Tian, Y., Margulies, D.S., Breakspear, M. et al.
       | Topographic organization of the human subcortex
       | unveiled with functional connectivity gradients.
       | Nature Neuroscience, Volume 23, Pages 1421–1432 (2020).
       | https://doi.org/10.1038/s41593-020-00711-6


Planned
~~~~~~~

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Publication
   * - Desikan-Killiany
     - | Desikan, R.S., Ségonne, F., Fischl, B. et al.
       | An automated labeling system for subdividing the human cerebral cortex
       | on MRI scans into gyral based regions of interest.
       | NeuroImage, Volume 31(3), Pages 968-980 (2006).
       | http://doi.org/10.1016/j.neuroimage.2006.01.021
   * - Glasser
     - | Glasser, M.F., Coalson, T.S., Robinson, E.C. et al.
       | A multi-modal parcellation of human cerebral cortex.
       | Nature (2016).
       | http://doi.org/10.1038/nature18933
   * - AAL
     - | Rolls, E.T., Huang, C.C., Lin, C.P., et al.
       | Automated anatomical labelling atlas 3.
       | Neuroimage, Volume 206 (2020).
       | https://doi.org/10.1016/j.neuroimage.2019.116189
   * - Shen
     - | Shen, X., Tokoglu, F., Papademetris, X., Constable, R.T.
       | Groupwise whole-brain parcellation from resting-state fMRI data
       | for network node identification.
       | Neuroimage, Volume 82 (2013).
       | https://doi.org/10.1016/j.neuroimage.2013.05.081.
   * - Mindboggle 101
     - | Klein, A., & Tourville, J.
       | 101 labeled brain images and a consistent human cortical labeling protocol.
       | Frontiers in Neuroscience (2012).
       | http://doi.org/10.3389/fnins.2012.00171/abstract
   * - Destrieux
     - | Destrieux, C., Fischl, B., Dale, A., & Halgren, E.
       | Automatic parcellation of human cortical gyri and sulci using standard
       | anatomical nomenclature.
       | NeuroImage, Volume 53(1), Pages 1–15 (2010).
       | http://doi.org/10.1016/j.neuroimage.2010.06.010.
   * - Fan
     - | Fan, L., Li, H., Zhuo, J. et al.
       | The human brainnetome atlas: a new brain atlas based on connectional
       | architecture.
       | Cerebral cortex, Volume 26(8), Pages 3508-3526 (2016).
       | https://doi.org/10.1093/cercor/bhw157
   * - Buckner
     - | Buckner, R.L., Krienen, F.M., Castellanos, A., Diaz, J.C., Yeo, B.T.T.
       | The organization of the human cerebellum estimated by intrinsic functional
       | connectivity.
       | Journal of Neurophysiology, Volume 106(5), Pages 2322–2345 (2011).
       | https://doi.org/10.1152/jn.00339.2011
       | Yeo, B.T.T., Krienen, F.M., Sepulcre, J. et al.
       | The organization of the human cerebral cortex estimated by intrinsic functional
       | connectivity.
       | Journal of Neurophysiology, Volume 106(3), Pages 1125–1165 (2011).
       | https://doi.org/10.1152/jn.00338.2011


Coordinates
-----------

Available
~~~~~~~~~

Planned
~~~~~~~

..
  helpful site for creating tables: https://rest-sphinx-memo.readthedocs.io/en/latest/ReST.html#tables
