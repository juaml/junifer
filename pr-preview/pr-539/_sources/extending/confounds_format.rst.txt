.. include:: ../links.inc

.. _adding_confounds_format:

Adding Confounds Format
=======================

#. Check :ref:`extending junifer <extending_extension>` on how to create a
   *junifer extension* if you have not done so.
#. Register the confounds format before defining / using a DataGrabber like so:

   .. code-block:: python

      from junifer.datagrabber import register_confounds_format
      ...


      # registers the confounds format as "confounds" and accessible as
      # ``ConfoundsFormat.Confounds``
      register_confounds_format(name="Confounds", alias="confounds")

      ...
