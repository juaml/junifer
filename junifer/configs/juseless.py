from ..datagrabber import DataladDataGrabber
from ..api.decorators import register_datagrabber


@register_datagrabber
class JuselessUKBVBM(DataladDataGrabber):
    """Juseless UKB VMG DataGrabber class.

    Implements a DataGrabber to access the UKB VBM data in Juseless.

    """

    def __init__(self, datadir=None):
        """Initialize a JuselessUKBVBM object.

        Parameters
        ----------
        datadir : str or Path
            That directory where the datalad dataset will be cloned. If None,
            (default), the datalad dataset will be cloned into a temporary
            directory.
        """
        uri = 'ria+http://ukb.ds.inm7.de#~cat_m0wp1'
        rootdir = 'm0wp1'
        types = ['VBM_GM']
        super().__init__(
            types=types, datadir=datadir, uri=uri, rootdir=rootdir)

    def get_elements(self):
        """Get the list of subjects in the dataset.

        Returns
        -------
        elements : list[str]
            The list of subjects in the dataset.
        """
        elems = []
        for x in self.datadir.glob('*._T1w.nii.gz'):
            sub, ses = x.name.split('_')
            sub = sub.replace('m0wp1', '')
            ses = ses[:5]
            elems.append((sub, ses))
        return elems

    def __getitem__(self, element):
        """Index one element in the dataset.

        Parameters
        ----------
        element : tuple[str, str]
            The element to be indexed. First element in the tuple is the
            subject, second element is the session.

        Returns
        -------
        out : dict[str -> Path]
            Dictionary of paths for each type of data required for the
            specified element.
        """
        sub, ses = element
        out = {}

        out['VBM_GM'] = self.datadir / f'm0wp1{sub}_{ses}_T1w.nii.gz'
        self._dataset_get(out)
        out['meta']['element'] = dict(subject=sub, session=ses)
        return out
