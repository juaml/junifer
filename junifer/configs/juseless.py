from ..datagrabber import PatternDataladDataGrabber
from ..api.decorators import register_datagrabber


@register_datagrabber
class JuselessDataladUKBVBM(PatternDataladDataGrabber):
    """Juseless UKB VBM DataGrabber class.

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
        replacements = ['subject', 'session']
        patterns = {
            'VBM_GM': 'm0wp1_sub-{subject}_ses-{session}_T1w.nii.gz'
        }
        super().__init__(
            types=types, datadir=datadir, uri=uri, rootdir=rootdir,
            replacements=replacements, patterns=patterns)
