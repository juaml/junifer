# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
from ..utils import logger


class PipelineStepMixin():

    def get_meta(self):
        t_meta = {}
        t_meta['class'] = self.__class__.__name__
        for k, v in vars(self).items():
            if not k.startswith('_'):
                t_meta[k] = v
        return t_meta

    def validate_input(self, input):
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input : Junifer Data dictionary
            The input to the pipeline step.

        Raises
        ------
        ValueError:
            If the input does not have the required data.
        """
        raise NotImplementedError('validate_input not implemented')

    def get_output_kind(self, input):
        """Get the kind of the pipeline step.

        Parameters
        ----------
        input : Junifer Data dictionary
            The input to the pipeline step.

        Returns
        -------
        output : Junifer Data dictionary
            The output of the pipeline step.
        """
        raise NotImplementedError('get_output_kind not implemented')

    def validate(self, input):
        """Validate the the pipeline step.

        Parameters
        ----------
        input : Junifer Data dictionary
            The input to the pipeline step.

        Returns
        -------
        output : Junifer Data dictionary
            The output of the pipeline step.

        Raises
        ------
        ValueError:
            If the input does not have the required data.
        """
        self.validate_input(input)
        return self.get_output_kind(input)

    def fit_transform(self, input):
        raise NotImplementedError('fit_transform not implemented')


class BaseMarker(PipelineStepMixin):
    """Base class for all markers."""

    def __init__(self, on, name=None):
        if not isinstance(on, list):
            on = [on]
        self._valid_inputs = on
        self.name = self.__class__.__name__ if name is None else name

    def get_meta(self):
        s_meta = super().get_meta()
        s_meta['name'] = self.name
        return dict(marker=s_meta)

    def validate_input(self, input):
        if not any(x in input for x in self._valid_inputs):
            raise ValueError(
                'Input does not have the required data.'
                f'\t Input: {input}'
                f'\t Required (any of): {self._valid_inputs}')

    def get_output_kind(self, input):
        return None

    def compute(self, input):
        raise NotImplementedError('compute not implemented')

    def fit_transform(self, input, storage=None):
        out = {}
        meta = input.get('meta', {})
        for kind in self._valid_inputs:
            if kind in input.keys():
                logger.info(f'Computing {kind}')
                t_input = input[kind]
                t_meta = meta.copy()
                t_meta.update(t_input.get('meta', {}))
                t_meta.update(self.get_meta())
                t_out = self.compute(t_input)
                t_out.update(meta=t_meta)
                if storage is not None:
                    storage.store_2d(**t_out)
                else:
                    out[kind] = t_out

        return out
