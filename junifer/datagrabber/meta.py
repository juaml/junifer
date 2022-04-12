from .base import BaseDataGrabber


class MultipleDataGrabber(BaseDataGrabber):
    def __init__(self, datagrabbers):
        # TODO: Check datagrabbers consistency
        # - same element keys
        # - no overlapping types
        self._datagrabbers = datagrabbers

    def get_types(self):
        types = [x for dg in self._datagrabbers for x in dg.get_types()]
        return types

    def get_meta(self):
        t_meta = {}
        t_meta['class'] = self.__class__.__name__
        t_meta['datagrabbers'] = [dg.get_meta() for dg in self._datagrabbers]

    def __enter__(self):
        for dg in self._datagrabbers:
            dg.__enter__()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        for dg in self._datagrabbers:
            dg.__exit__(exc_type, exc_value, exc_traceback)

    def __getitem__(self, element):
        out = {}
        for dg in self._datagrabbers:
            t_out = dg[element]
            out.update(t_out)
