.. include:: ../links.inc

.. _adding_data_dump_assets:

Adding Data Dump Assets
=======================

``junifer`` supports dumping ``nibabel.Nifti1Image`` and ``pandas.DataFrame`` which should cover most fMRI use cases. But, in case you work with other modalities like EEG, you can register your own data dump asset.

How to add a data dump asset
----------------------------

This example shows how to create a data dump asset for ``mne.io.Raw``.

#. Check :ref:`extending junifer <extending_extension>` on how to create a
   *junifer extension* if you have not done so.
#. Create the data registry in the *extension script* like so:

   .. code-block:: python

    from pathlib import Path

    from junifer.api.decorators import register_data_dump_asset
    from junifer.pipeline import BaseDataDumpAsset

    import mne

    @register_data_dump_asset([mne.io.Raw], [".fif", ".fif.gz"])
    class RawAsset(BaseDataDumpAsset):
        """Class for ``mne.io.Raw`` dumper."""

        def dump(self) -> None:
            self.data.save(self.path_without_ext.with_suffix(".raw.fif.gz"))

        @classmethod
        def load(cls: "RawAsset", path: Path) -> mne.io.Raw:
            return mne.io.Raw(path)

   * :func:`.register_data_dump_asset` registers a class. The first argument is
     a list of types that the class is responsible for saving and the second
     argument is a list of file extensions that the class is responsible for
     loading.
   * Inheriting from ``junifer.pipeline.BaseDumpAsset`` takes care of the class
     acting as a data dump asset.
   * Method ``junifer.pipeline.BaseDumpAsset.dump`` and class method
     ``junifer.pipeline.BaseDumpAsset.load`` need to be implemented.
