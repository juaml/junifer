.. include:: links.inc

FAQs
====

How do I contribute to junifer?
-------------------------------
Please follow the :ref:`contribution guidelines <contribution_guidelines>`.


How do I set up VSCode for contribution?
----------------------------------------

The :ref:`contribution guidelines <contribution_guidelines>`
apply in general when using VSCode as your IDE as well.

The following steps are specific to VSCode and you can choose to go with it:

1. After forking the repository on GitHub, you can clone the forked repository
   using the internal version control tool.

2. We recommend using ``conda`` to create your virtual environment

   .. code-block:: bash

       conda env create -n <your-environment-name> -f conda-env.yml
       conda activate <your-environment-name>

   The ``conda-env.yml`` can be found at the root of the repository.

The required development tools should be installed and you should be good to go.
