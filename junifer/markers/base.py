# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

class PipelineStepMixin():

    @property
    def name(self):
        return self.__class__.__name__

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
