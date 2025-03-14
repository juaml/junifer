.. include:: links.inc

.. _builtin:

Built-in Pipeline Components
============================


Data Grabber
------------

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

    Version added: If the status is "Done", the junifer version in which the
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
   * - :class:`.DataladHCP1200`
     - `HCP OpenAccess dataset <https://github.com/datalad-datasets/human-connectome-project-openaccess>`_
     - Open with registration
     - Built-in
     - Done
     - 0.0.1
   * - :class:`.JuselessDataladUKBVBM`
     - | UKB VBM dataset preprocessed with CAT.
       | Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1
   * - :class:`.JuselessDataladCamCANVBM`
     - | CamCAN VBM dataset preprocessed with CAT.
       | Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1
   * - :class:`.DataladAOMICID1000`
     - `AOMIC 1000 dataset <https://github.com/OpenNeuroDatasets/ds003097>`_
     - Open without registration
     - Built-in
     - Done
     - 0.0.1
   * - :class:`.DataladAOMICPIOP1`
     - `AOMIC PIOP1 dataset <https://github.com/OpenNeuroDatasets/ds002785>`_
     - Open without registration
     - Built-in
     - Done
     - 0.0.1
   * - :class:`.DataladAOMICPIOP2`
     - `AOMIC PIOP2 dataset <https://github.com/OpenNeuroDatasets/ds002790>`_
     - Open without registration
     - Built-in
     - Done
     - 0.0.1
   * - :class:`.JuselessDataladAOMICID1000VBM`
     - | AOMIC ID1000 VBM dataset.
       | Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1
   * - :class:`.JuselessDataladIXIVBM`
     - | `IXI VBM dataset <https://brain-development.org/ixi-dataset/>`_.
       | Available for Juseless only.
     - Restricted
     - ``junifer.configs.juseless``
     - Done
     - 0.0.1
   * - :class:`.JuselessUCLA`
     - | UCLA fMRIPrep dataset.
       | Available for Juseless only.
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


Preprocessor
------------

..
    Provide a list of the Preprocessors that are implemented or planned.

    State: this should indicate the state of the preprocessor. Valid options are
    - Planned
    - In Progress
    - Done

    Version added: If the status is "Done", the junifer version in which the
    preprocessor was added. Else, a link to the Github issue or pull request
    implementing the preprocessor. Links to github can be added by using the
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
   * - :class:`.fMRIPrepConfoundRemover`
     - Remove confounds from ``fMRIPrep``-ed data
     - Done
     - 0.0.1
   * - :class:`.SpaceWarper`
     - | Warp / transform data from one space to another
       | (subject-native or other template spaces)
     - Done
     - 0.0.4
   * - ``Smoothing``
     - | Apply smoothing to data, particularly useful when dealing with
       | ``fMRIPrep``-ed data
     - In Progress
     - :gh:`161`


..
   Planned
   ~~~~~~~


Marker
------

..
    Provide a list of the Markers that are implemented or planned.

    State: this should indicate the state of the marker. Valid options are
    - Planned
    - In Progress
    - Done

    Version added: If the status is "Done", the junifer version in which the
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
   * - :class:`.ParcelAggregation`
     - Apply parcellation and perform aggregation function
     - Done
     - 0.0.1
   * - :class:`.FunctionalConnectivityParcels`
     - Compute functional connectivity over parcellation
     - Done
     - 0.0.1
   * - :class:`.CrossParcellationFC`
     - Compute functional connectivity across two parcellations
     - Done
     - 0.0.1
   * - :class:`.SphereAggregation`
     - Spherical aggregation using mean
     - Done
     - 0.0.1
   * - :class:`.FunctionalConnectivitySpheres`
     - Compute functional connectivity over spheres placed on coordinates
     - Done
     - 0.0.1
   * - :class:`.RSSETSMarker`
     - Compute root sum of squares of edgewise timeseries
     - Done
     - 0.0.1
   * - :class:`.ReHoParcels`
     - Calculate regional homogeneity over parcellation
     - Done
     - 0.0.1
   * - :class:`.ReHoSpheres`
     - Calculate regional homogeneity over spheres placed on coordinates
     - Done
     - 0.0.1
   * - :class:`.ALFFParcels`
     - Calculate (f)ALFF and aggregate using parcellations
     - Done
     - 0.0.1
   * - :class:`.ALFFSpheres`
     - Calculate (f)ALFF and aggregate using spheres placed on coordinates
     - Done
     - 0.0.1
   * - :class:`.EdgeCentricFCParcels`
     - | Calculate edge-centric functional connectivity over parcellation, as
       | found in
       | `Jo et al. (2021) <https://doi.org/10.1016/j.neuroimage.2021.118204>`_
     - Done
     - 0.0.2
   * - :class:`.EdgeCentricFCSpheres`
     - | Calculate edge-centric functional connectivity over spheres placed on
       | coordinates, as found in
       | `Jo et al. (2021) <https://doi.org/10.1016/j.neuroimage.2021.118204>`_
     - Done
     - 0.0.2
   * - :class:`.TemporalSNRParcels`
     - Calculate temporal signal-to-noise ratio using parcellations
     - Done
     - 0.0.2
   * - :class:`.TemporalSNRSpheres`
     - | Calculate temporal signal-to-noise ratio using spheres placed on
       | coordinates
     - Done
     - 0.0.2
   * - :class:`.HurstExponent`
     - | Calculate Hurst exponent of a time series as found in
       | `Peng et al. (1995) <https://doi.org/10.1063/1.166141>`_
     - Done
     - 0.0.4
   * - :class:`.MultiscaleEntropyAUC`
     - | Calculate AUC of multiscale entropy of a time series as found in
       | `Costa et al. (2002) <https://doi.org/10.1103/PhysRevLett.89.068102>`_
     - Done
     - 0.0.4
   * - :class:`.PermEntropy`
     - | Calculate permutation entropy of a time series as found in
       | `Bandt at al. (2002) <https://doi.org/10.1103/PhysRevLett.88.174102>`_
     - Done
     - 0.0.4
   * - :class:`.RangeEntropy`
     - | Calculate range entropy of a time series as found in
       | `Omidvarnia et al. (2018) <https://doi.org/10.3390/e20120962>`_
     - Done
     - 0.0.4
   * - :class:`.RangeEntropyAUC`
     - | Calculate AUC of range entropy of a time series as found in
       | `Omidvarnia et al. (2018) <https://doi.org/10.3390/e20120962>`_
     - Done
     - 0.0.4
   * - :class:`.SampleEntropy`
     - | Calculate sample entropy of a time series as found in
       | `Richman et al. (2000) <https://doi.org/10.1152/ajpheart.2000.278.6.H2039>`_
     - Done
     - 0.0.4

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

Parcellation
------------

..
    Provide a list of the Parcellations that are implemented or planned.

    Version added: The junifer version in which the parcellation was added.

Available
~~~~~~~~~

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Options
     - Keys
     - Template Spaces
     - Version Added
     - Publication
   * - Schaefer
     - ``n_rois``, ``yeo_networks``
     - | ``Schaefer900x7``, ``Schaefer1000x7``, ``Schaefer100x17``,
       | ``Schaefer200x17``, ``Schaefer300x17``, ``Schaefer400x17``,
       | ``Schaefer500x17``, ``Schaefer600x17``, ``Schaefer700x17``,
       | ``Schaefer800x17``, ``Schaefer900x17``, ``Schaefer1000x17``
     - ``MNI152NLin6Asym``
     - 0.0.1
     - | Schaefer, A., Kong, R., Gordon, E.M. et al.
       | Local-Global Parcellation of the Human Cerebral Cortex from
       | Intrinsic Functional Connectivity MRI
       | Cerebral Cortex, Volume 28(9), Pages 3095–3114 (2018).
       | https://doi.org/10.1093/cercor/bhx179
   * - SUIT
     - ``space``
     - ``SUITxMNI``, ``SUITxSUIT``
     - ``SUIT``, ``MNI152Lin6Asym``
     - 0.0.1
     - | Diedrichsen, J.
       | A spatially unbiased atlas template of the human cerebellum.
       | NeuroImage, Volume 33(1), Pages 127–138 (2006).
       | https://doi.org/10.1016/j.neuroimage.2006.05.056
   * - Tian
     - ``scale``, ``space``, ``magneticfield``
     - | ``TianxS1x3TxMNI6thgeneration``, ``TianxS1x7TxMNI6thgeneration``,
       | ``TianxS2x3TxMNI6thgeneration``, ``TianxS2x7TxMNI6thgeneration``,
       | ``TianxS3x3TxMNI6thgeneration``, ``TianxS3x7TxMNI6thgeneration``,
       | ``TianxS4x3TxMNI6thgeneration``, ``TianxS4x7TxMNI6thgeneration``,
       | ``TianxS1x3TxMNInonlinear2009cAsym``,
       | ``TianxS2x3TxMNInonlinear2009cAsym``,
       | ``TianxS3x3TxMNInonlinear2009cAsym``,
       | ``TianxS4x3TxMNInonlinear2009cAsym``
     - ``MNI152NLin6Asym``, ``MNI152NLin2009cAsym``
     - 0.0.1
     - | Tian, Y., Margulies, D.S., Breakspear, M. et al.
       | Topographic organization of the human subcortex
       | unveiled with functional connectivity gradients.
       | Nature Neuroscience, Volume 23, Pages 1421–1432 (2020).
       | https://doi.org/10.1038/s41593-020-00711-6
   * - AICHA
     - ``version``
     - ``AICHA_v1``, ``AICHA_v2``
     - ``MNI152Lin6Asym``
     - 0.0.3
     - | Joliot, M., Jobard, G., Naveau, M. et al.
       | AICHA: An atlas of intrinsic connectivity of homotopic areas.
       | Journal of Neuroscience Methods, Volume 254, Pages 46-59 (2015).
       | https://doi.org/10.1016/j.jneumeth.2015.07.013
   * - Shen
     - ``year``, ``n_rois``
     - | ``Shen_2013_50``, ``Shen_2013_100``, ``Shen_2013_150``,
       | ``Shen_2015_268``, ``Shen_2019_368``
     - ``MNI152NLin2009cAsym``
     - 0.0.3
     - | Shen, X., Tokoglu, F., Papademetris, X., Constable, R.T.
       | Groupwise whole-brain parcellation from resting-state fMRI data
       | for network node identification.
       | NeuroImage, Volume 82 (2013).
       | https://doi.org/10.1016/j.neuroimage.2013.05.081.
       | Finn, E.S., Shen, X., Scheinost, D., et al.
       | Functional connectome fingerprinting: identifying individuals using
       | patterns of brain connectivity.
       | Nature Neuroscience, Volume 18(11), Pages 1664-1671 (2015).
       | https://doi:10.1038/nn.4135
   * - Yan
     - ``n_rois``, ``yeo_networks``, ``kong_networks``
     - | ``Yan100xYeo7``, ``Yan200xYeo7``, ``Yan300xYeo7``,
       | ``Yan400xYeo7``, ``Yan500xYeo7``, ``Yan600xYeo7``,
       | ``Yan700xYeo7``, ``Yan800xYeo7``, ``Yan900xYeo7``,
       | ``Yan1000xYeo7``,
       | ``Yan100xYeo17``, ``Yan200xYeo17``, ``Yan300xYeo17``,
       | ``Yan400xYeo17``, ``Yan500xYeo17``, ``Yan600xYeo17``,
       | ``Yan700xYeo17``, ``Yan800xYeo17``, ``Yan900xYeo17``,
       | ``Yan1000xYeo17``,
       | ``Yan100xKong17``, ``Yan200xKong17``, ``Yan300xKong17``,
       | ``Yan400xKong17``, ``Yan500xKong17``, ``Yan600xKong17``,
       | ``Yan700xKong17``, ``Yan800xKong17``, ``Yan900xKong17``,
       | ``Yan1000xKong17``
     - ``MNI152NLin6Asym``
     - 0.0.3
     - | Yan, X., Kong, R., Xue, A., et al.
       | Homotopic local-global parcellation of the human cerebral cortex from
       | resting-state functional connectivity.
       | NeuroImage, Volume 273 (2023).
       | https://doi.org/10.1016/j.neuroimage.2023.120010
   * - Brainnetome
     - ``threshold``
     - ``Brainnetome_thr0``, ``Brainnetome_thr25``, ``Brainnetome_thr50``
     - ``MNI152NLin6Asym``
     - 0.0.4
     - | Fan, L., Li, H., Zhuo, J., et al.
       | The Human Brainnetome Atlas: A New Brain Atlas Based on Connectional
       | Architecture
       | Cerebral Cortex, Volume 26(8), Pages 3508–3526 (2016).
       | https://doi.org/10.1093/cercor/bhw157


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
       | NeuroImage, Volume 206 (2020).
       | https://doi.org/10.1016/j.neuroimage.2019.116189
   * - Mindboggle 101
     - | Klein, A., & Tourville, J.
       | 101 labeled brain images and a consistent human cortical labeling
       | protocol.
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
       | The organization of the human cerebellum estimated by intrinsic
       | functional connectivity.
       | Journal of Neurophysiology, Volume 106(5), Pages 2322–2345 (2011).
       | https://doi.org/10.1152/jn.00339.2011
       | Yeo, B.T.T., Krienen, F.M., Sepulcre, J. et al.
       | The organization of the human cerebral cortex estimated by intrinsic
       | functional connectivity.
       | Journal of Neurophysiology, Volume 106(3), Pages 1125–1165 (2011).
       | https://doi.org/10.1152/jn.00338.2011


Coordinates
-----------

..
    Provide a list of the Coordinates that are implemented or planned.

    Version added: The junifer version in which the parcellation was added.

Available
~~~~~~~~~

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Keys
     - Version Added
     - Publication
   * - Cognitive action control
     - ``CogAC``
     - 0.0.1
     - | Cieslik, E.C., Mueller, V.I., Eickhoff, C.R., Langner, R.,
       | Eickhoff, S.B.
       | Three key regions for supervisory attentional control: Evidence from
       | neuroimaging meta-analyses.
       | Neuroscience & Biobehavioral Reviews, Volume 48, Pages 22-34 (2015).
       | https://doi.org/10.1016/j.neubiorev.2014.11.003.
   * - Cognitive action regulation
     - ``CogAR``
     - 0.0.1
     - | Langner, R., Leiberg, S., Hoffstaedter, F., Eickhoff, S.B.
       | Towards a human self-regulation system: Common and distinct neural
       | signatures of emotional and behavioural control.
       | Neuroscience & Biobehavioral Reviews, Volume 90, Pages 400-410 (2018).
       | https://doi.org/10.1016/j.neubiorev.2018.04.022.
   * - Default mode network
     - ``DMNBuckner``
     - 0.0.1
     - | Van Dijk, K.R., Hedden, T., Venkataraman, A. et al.
       | Intrinsic functional connectivity as a tool for human connectomics:
       | theory, properties, and optimization.
       | Journal of neurophysiology, Volume 103(1), Pages 297-321 (2010).
       | https://doi.org/10.1152/jn.00783.2009
       | Buckner, R.L., Andrews‐Hanna, J.R., & Schacter, D.L.
       | The brain's default network: anatomy, function, and relevance to
       | disease.
       | Annals of the New York Academy of Sciences, Volume 1124(1), Pages 1-38
       | (2008).
       | https://doi.org/10.1196/annals.1440.011
   * - Missing formal name
     - ``extDMN``
     - 0.0.1
     - Missing publication details
   * - Empathic processing
     - ``Empathy``
     - 0.0.1
     - | Bzdok, D., Schilbach, L., Vogeley, K. et al.
       | Parsing the neural correlates of moral cognition: ALE meta-analysis on
       | morality, theory of mind, and empathy.
       | Brain Structure and Function, Volume 217(4), Pages 783-796 (2012).
       | https://doi.org/10.1007/s00429-012-0380-y
   * - Extended social-affective default
     - ``eSAD``
     - 0.0.1
     - | Amft, M., Bzdok, D., Laird, A.R. et al.
       | Definition and characterization of an extended social-affective default
       | network.
       | Brain structure & function, Volume 220, Pages 1031–1049 (2015).
       | https://doi.org/10.1007/s00429-013-0698-0
   * - Extended multiple-demand network
     - ``eMDN``
     - 0.0.1
     - | Camilleri, J.A., Müller, V.I., Fox, P. et al.
       | Definition and characterization of an extended multiple-demand network.
       | NeuroImage, Volume 165, Pages 138-147 (2018).
       | https://doi.org/10.1016/j.neuroimage.2017.10.020.
   * - Motor execution
     - ``Motor``
     - 0.0.1
     - | Witt, S.T., Laird, A.R., Meyerand, M.E.
       | Functional neuroimaging correlates of finger-tapping task variations:
       | An ALE meta-analysis,
       | NeuroImage, Volume 42(1), Pages 343-356 (2008).
       | https://doi.org/10.1016/j.neuroimage.2008.04.025.
   * - Multitasking
     - ``MultiTask``
     - 0.0.1
     - | Worringer, B., Langner, R., Koch, I. et al.
       | Common and distinct neural correlates of dual-tasking and
       | task-switching: a meta-analytic review and a neuro-cognitive processing
       | model of human multitasking.
       | Brain structure & function, Volume 224(5), Pages 1845–1869 (2019).
       | https://doi.org/10.1007/s00429-019-01870-4
   * - Physiological stress
     - ``PhysioStress``
     - 0.0.1
     - | Kogler, L., Müller, V.I., Chang, A. et al.
       | Psychosocial versus physiological stress — Meta-analyses on
       | deactivations and activations of the neural correlates of stress
       | reactions.
       | NeuroImage, Volume 119, Pages 235-251 (2015).
       | https://doi.org/10.1016/j.neuroimage.2015.06.059.
   * - Reward-related decision making
     - ``Rew``
     - 0.0.1
     - | Liu, X., Hairston, J., Schrier, M., Fan, J.
       | Common and distinct networks underlying reward valence and processing
       | stages: A meta-analysis of functional neuroimaging studies.
       | Neuroscience & Biobehavioral Reviews, Volume 35(5), Pages 1219-1236
       | (2011).
       | https://doi.org/10.1016/j.neubiorev.2010.12.012.
   * - Missing formal name
     - ``Somatosensory``
     - 0.0.1
     - Missing publication details
   * - Theory-of-mind cognition
     - ``ToM``
     - 0.0.1
     - | Bzdok, D., Schilbach, L., Vogeley, K. et al.
       | Parsing the neural correlates of moral cognition: ALE meta-analysis on
       | morality, theory of mind, and empathy.
       | Brain Structure and Function, Volume 217(4), Pages 783-796 (2012).
       | https://doi.org/10.1007/s00429-012-0380-y
   * - Vigilant attention
     - ``VigAtt``
     - 0.0.1
     - | Langner, R., & Eickhoff, S.B.
       | Sustaining attention to simple tasks: a meta-analytic review of the
       | neural mechanisms of vigilant attention.
       | Psychological bulletin, Volume 139 4, Pages 870-900 (2013).
       | https://doi.org/10.1037/a0030694
   * - Working memory
     - ``WM``
     - 0.0.1
     - | Rottschy, C., Langner, R., Dogan, I. et al.
       | Modelling neural correlates of working memory: A coordinate-based
       | meta-analysis.
       | NeuroImage, Volume 60, Pages 830-846 (2012).
       | https://doi.org/10.1016/j.neuroimage.2011.11.050.
   * - Areal functional network from Power et al. (2011)
     - ``Power2011``
     - 0.0.2
     - | Power, J. D., Cohen, A. L., Nelson, S. M. et al.
       | Functional network organization of the human brain.
       | Neuron, Volume 72(4), Pages 665–678 (2011).
       | https://doi.org/10.1016/j.neuron.2011.09.006
   * - Brain maturity functional connections from Dosenbach et al. (2010)
     - ``Dosenbach``
     - 0.0.2
     - | Dosenbach, N.U.F., Nardos, B., Cohen, A.L. et al.
       | Prediction of Individual Brain Maturity Using fMRI
       | Science, Volume 329(5997), Pages 1358-1361 (2010).
       | https://doi.org/10.1126/science.1194144
   * - Autobiographical Memory from Spreng et al. (2009)
     - ``AutobiographicalMemory``
     - 0.0.4
     - | Spreng, R. N., Mar, R. A., Kim, A. S. N.
       | The Common Neural Basis of Autobiographical Memory, Prospection,
       | Navigation, Theory of Mind, and the Default Mode: A Quantitative
       | Meta-analysis.
       | Journal of Cognitive Neuroscience, Volume 21(3), Pages 489–510 (2009).
       | https://doi.org/10.1162/jocn.2008.21029
   * - | Functionally-constrained ROIs from non-cortical structures from
       | Seitzman et al. (2020)
     - ``Seitzman2018``
     - 0.0.6
     - | Seitzman, B. A., Gratton, C., Marek, S. et al.
       | A set of functionally-defined brain regions with improved representation
       | of the subcortex and cerebellum.
       | NeuroImage, Volume 206 (2020).
       | https://doi.org/10.1016/j.neuroimage.2019.116290


Planned
~~~~~~~

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Publication
   * - Emotional scene and face processing (EmoSF)
     - | Sabatinelli, D., Fortune, E.E., Li, Q. et al.
       | Emotional perception: Meta-analyses of face and natural scene
       | processing.
       | NeuroImage, Volume 54(3), Pages 2524-2533 (2011).
       | https://doi.org/10.1016/j.neuroimage.2010.10.011.
   * - Perceptuo-motor network
     - | Heckner, M.K., Cieslik, E.C., Eickhoff, S.B. et al.
       | The Aging Brain and Executive Functions Revisited: Implications from
       | Meta-analytic and Functional-Connectivity Evidence.
       | Journal of Cognitive Neuroscience, Volume 33(9), Pages 1716–1752 (2021).
       | https://doi.org/10.1162/jocn_a_01616


Mask
----

..
    Provide a list of the masks that are implemented or planned.

    Version added: The junifer version in which the mask was added.

Available
~~~~~~~~~

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Keys
     - Template Space
     - Version Added
     - Description - Publication
   * - Vickery-Patil (Gray Matter)
     - | ``GM_prob0.2``
     - ``MNI152Lin6Asym``
     - 0.0.1
     - | Vickery, Sam, & Patil, Kaustubh. (2022).
       | Chimpanzee and Human Gray Matter Masks [Data set]. Zenodo.
       | https://doi.org/10.5281/zenodo.6463123
   * - Vickery-Patil (Cortex + Basal Ganglia)
     - | ``GM_prob0.2_cortex``
     - ``MNI152Lin6Asym``
     - 0.0.1
     - | Vickery, Sam, & Patil, Kaustubh. (2022).
       | Chimpanzee and Human Gray Matter Masks [Data set]. Zenodo.
       | https://doi.org/10.5281/zenodo.6463123
   * - ``junifer``'s custom brain mask
     - | ``compute_brain_mask``
     - Adapts to the target data
     - 0.0.2
     - | Compute the whole-brain, gray-matter or white-matter mask using
       | the template and the resolution from the target image. The
       | templates are obtained via ``templateflow``.
   * - ``nilearn``'s mask computed from fMRI data
     - | ``compute_epi_mask``
     - Adapts to the target data
     - 0.0.2
     - | Compute a brain mask from fMRI data. This is based on an heuristic
       | proposed by T.Nichols: find the least dense point of the histogram,
       | between fractions ``lower_cutoff`` and ``upper_cutoff`` of the total
       | image histogram. See :func:`nilearn.masking.compute_epi_mask`
   * - ``nilearn``'s background mask
     - | ``compute_background_mask``
     - Adapts to the target data
     - 0.0.2
     - | Compute a brain mask for the images by guessing the value of the
       | background from the border of the image.
       | See :func:`nilearn.masking.compute_background_mask`

..
   Planned
   ~~~~~~~

..
  helpful site for creating tables: https://rest-sphinx-memo.readthedocs.io/en/latest/ReST.html#tables
