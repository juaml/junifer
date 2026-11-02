.. include:: links.inc

.. _starting:

First steps with ``junifer``
============================

.. note::

   To scroll the graph left and right, click on the graph and use the arrows on your keyboard.

.. mermaid::

   flowchart TD
     start((( Start )))
     read_understanding(Read Understanding junifer)
     start --> read_understanding
     question_features{Can I compute\nthe features I want\nusing junifer?}
     read_understanding --> question_features
     question_features -->|Yes| read_using_final
     question_features -->|I'm not sure| read_using
     question_features -->|No| question_feature_type
     read_using --> question_features

     read_using(Read Using junifer)

     question_feature_type{"What am I missing\nfrom junifer"}
     question_feature_type --> missing_datagrabber
     question_feature_type --> missing_preprocessing
     question_feature_type --> missing_marker
     question_feature_type --> missing_other
     missing_datagrabber("A Dataset/DataGrabber")
     missing_preprocessing("A Preprocessor")
     missing_marker("A Marker")
     missing_other("Something else")

     missing_datagrabber --> question_datagrabber_junifarm
     question_datagrabber_junifarm{Is the\ndataset/datagrabber\nin juni-farm?}
     question_datagrabber_junifarm -->|Yes| read_using_final
     question_datagrabber_junifarm -->|No| read_extending_datagrabber_start
     read_extending_datagrabber_start(Read Creating a junifer extension)
     read_extending_datagrabber_start --> read_extending_datagrabber
     read_extending_datagrabber(Read Creating Data Grabbers)
     read_extending_datagrabber --> question_datagrabber_kind
     question_datagrabber_kind{Is your dataset\na datalad one?}
     question_datagrabber_kind -->|Yes| extend_datagrabber_datalad
     question_datagrabber_kind -->|No| extend_datagrabber_pattern
     extend_datagrabber_pattern(Use\nPatternDataGrabber)
     extend_datagrabber_datalad(Use\nPatternDataladDataGrabber)
     extend_datagrabber_pattern --> question_datagrabber_solved
     extend_datagrabber_datalad --> question_datagrabber_solved
     question_datagrabber_solved{Can you use\nyour data now?}
     question_datagrabber_solved -->|Yes| question_contribute_datagrabber
     question_datagrabber_solved -->|No| contact_help
     question_contribute_datagrabber{Do you think\nyour DataGrabber\nis useful for other users?}
     question_contribute_datagrabber -->|Yes| contribute_datagrabber
     question_contribute_datagrabber -->|No| final_run
     contribute_datagrabber(Create a\nDATASET REQUEST\nissue on GitHub)
     contribute_datagrabber --> final_run

     missing_marker --> question_marker_junifarm
     question_marker_junifarm{Is the marker\nin juni-farm?}
     question_marker_junifarm -->|Yes| read_using_final
     question_marker_junifarm -->|No| read_extending_marker_start
     read_extending_marker_start(Read Creating a junifer extension)
     read_extending_marker_start --> read_extending_marker
     read_extending_marker(Read Creating Markers)
     read_extending_marker --> question_marker_solved
     question_marker_solved{Can you use\nyour marker now?}
     question_marker_solved -->|Yes| question_contribute_marker
     question_marker_solved -->|No| contact_help
     question_contribute_marker{Do you think\nyour Marker\nis useful for other users?}
     question_contribute_marker -->|Yes| contribute_marker
     question_contribute_marker -->|No| final_run
     contribute_marker(Create a\nMARKER REQUEST\nissue on GitHub)
     contribute_marker --> final_run

     missing_preprocessing --> contact_help

     missing_mask{"A Mask?"}
     missing_parcellation{"A Parcellation?"}
     missing_coordinates{"Coordinates?"}
     missing_other_other{"Something else?"}
     missing_other --> missing_mask
     missing_other --> missing_parcellation
     missing_other --> missing_coordinates
     missing_other --> missing_other_other
     missing_other_other --> contact_help

     contact_help(((Contact the\njunifer team)))

     missing_mask --> read_adding_mask_start
     read_adding_mask_start("Read Creating a junifer extension")
     read_adding_mask_start --> read_adding_mask
     read_adding_mask("Read Adding Masks")
     read_adding_mask --> missing_other_solved

     missing_parcellation --> read_adding_parcellation_start
     read_adding_parcellation_start("Read Creating a junifer extension")
     read_adding_parcellation_start --> read_adding_parcellation
     read_adding_parcellation("Read Adding Parcellations")
     read_adding_parcellation --> missing_other_solved

     missing_coordinates --> read_adding_coordinates_start
     read_adding_coordinates_start("Read Creating a junifer extension")
     read_adding_coordinates_start --> read_adding_coordinates
     read_adding_coordinates("Read Adding Coordinates")
     read_adding_coordinates --> missing_other_solved

     missing_other_solved{Did you solve your issue?}
     missing_other_solved -->|Yes| read_using_final
     missing_other_solved -->|No| missing_other_contact
     missing_other_contact(Contact the\njunifer team)
     missing_other_contact --> missing_other_issue
     missing_other_issue(((Submit a\nFEATURE REQUEST\nissue in GitHub)))

     read_using_final(Read Using junifer)
     read_using_final --> final_yaml
     final_yaml(Create/edit the YAML file)
     final_yaml --> final_run
     final_run(Use junifer run to test your YAML configuration)
     final_run --> question_final_run_worked
     question_final_run_worked{"Did it work?"}
     question_final_run_worked -->|No| question_error_run
     question_error_run{"Is it an issue\nwith my YAML file?"}
     question_error_run -->|Yes| final_yaml
     question_error_run -->|No| error_contact
     error_contact(Contact the\njunifer team)
     error_contact --> error_issue
     error_issue(((Submit a\nBUG REPORT issue\nin GitHub)))
     question_final_run_worked -->|Yes| final_queue
     final_queue(Use junifer queue to compute your features)
     final_queue --> final_magic
     final_magic(((Let junifer do its magic!)))

     click read_understanding href "https://juaml.github.io/junifer/main/understanding/index.html"
     click read_using href "https://juaml.github.io/junifer/main/using/index.html"
     click read_using_final href "https://juaml.github.io/junifer/main/using/index.html"
     click read_extending_datagrabber_start href "https://juaml.github.io/junifer/main/extending/extension.html"
     click read_extending_datagrabber href "https://juaml.github.io/junifer/main/extending/datagrabber.html"
     click read_extending_marker_start href "https://juaml.github.io/junifer/main/extending/extension.html"
     click read_extending_marker href "https://juaml.github.io/junifer/main/extending/marker.html"
     click read_adding_mask_start href "https://juaml.github.io/junifer/main/extending/extension.html"
     click read_adding_mask href "https://juaml.github.io/junifer/main/extending/masks.html"
     click read_adding_parcellation_start href "https://juaml.github.io/junifer/main/extending/extension.html"
     click read_adding_parcellation href "https://juaml.github.io/junifer/main/extending/parcellations.html"
     click read_adding_coordinates_start href "https://juaml.github.io/junifer/main/extending/extension.html"
     click read_adding_coordinates href "https://juaml.github.io/junifer/main/extending/coordinates.html"

     click error_issue href "https://github.com/juaml/junifer/issues/new/choose" _blank
     click missing_other_issue href "https://github.com/juaml/junifer/issues/new/choose" _blank
     click contribute_marker href "https://github.com/juaml/junifer/issues/new/choose" _blank
     click contribute_datagrabber href "https://github.com/juaml/junifer/issues/new/choose" _blank

     click error_contact href "https://juaml.github.io/junifer/main/help.html"
     click contact_help href "https://juaml.github.io/junifer/main/help.html"
     click missing_other_contact href "https://juaml.github.io/junifer/main/help.html"
