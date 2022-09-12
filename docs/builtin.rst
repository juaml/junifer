
Available pipeline steps
========================


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

.. list-table:: Available data grabbers
   :widths: auto
   :header-rows: 1

   * - Class
     - Description
     - Access
     - Type/Config
     - State
     - Version Added
   * - `DataladHCP1200`
     - `HCP OpenAccess dataset <https://github.com/datalad-datasets/human-connectome-project-openaccess>`_
     - Open with registration
     - Built-in
     - In Progress
     - :gh:`4`
   * - `JuselessDataladUKBVBM`
     - UKB VBM dataset preprocessed with CAT. Available for Juseless only
     - Restricted
     - `junifer.configs.juseless`
     - Done
     - 0.0.1



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

.. list-table:: Available data grabbers
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



Available Atlases and Coordinates
=================================

+------------------+-----------------------+-----------------------------+---------------+
| Name             | Options               | Keys                        | Version Added |
+==================+=======================+=============================+===============+
| Schaefer         | `n_rois`              | `Schaefer100x7`             | 0.0.1         |
|                  | `yeo_networks`        | `Schaefer200x7`             |               |
|                  |                       | `Schaefer300x7`             |               |
|                  |                       | `Schaefer400x7`             |               |
|                  |                       | `Schaefer500x7`             |               |
|                  |                       | `Schaefer600x7`             |               |
|                  |                       | `Schaefer700x7`             |               |
|                  |                       | `Schaefer800x7`             |               |
|                  |                       | `Schaefer900x7`             |               |
|                  |                       | `Schaefer1000x7`            |               |
|                  |                       | `Schaefer100x17`            |               |
|                  |                       | `Schaefer200x17`            |               |
|                  |                       | `Schaefer300x17`            |               |
|                  |                       | `Schaefer400x17`            |               |
|                  |                       | `Schaefer500x17`            |               |
|                  |                       | `Schaefer600x17`            |               |
|                  |                       | `Schaefer700x17`            |               |
|                  |                       | `Schaefer800x17`            |               |
|                  |                       | `Schaefer900x17`            |               |
|                  |                       | `Schaefer1000x17`           |               |
+------------------+-----------------------+-----------------------------+---------------+
