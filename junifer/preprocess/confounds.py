import numpy as np

from junifer.markers.base import PipelineStepMixin

class BaseConfoundRemover(PipelineStepMixin):
    """ A base class to read confound files and select columns according to 
    a pre-defined strategy
    
    """

    # TODO: Properly Validate Input
    # TODO: implement get_output_kind
    # TODO: implement fit_transform

    # lower priority
    # TODO: implement more strategies from 
    # nilearn.interfaces.fmriprep.load_confounds for Felix's confound files,
    # in particular scrubbing
    # TODO: Implement read_confounds for fmriprep data

    def __init__(self, strategy):
        """ Initialise a BaseConfoundReader object
        
        Parameters
        -----------
        strategy : dict
            keys of dictionary should correspond to names of noise components
            to include:
            - 'motion'
            - 'wm_csf'
            - 'global_signal'
            values of dictionary should correspond to types of confounds 
            extracted from each signal:
            - 'basic' - only the confounding time series
            - 'power2' - signal + quadratic term
            - 'derivatives' - signal + derivatives
            - 'full' - signal + deriv. + quadratic terms + power2 deriv.
        """
        self.strategy = strategy


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
        for k, v in self.strategy.items():
            if k not in ['motion','wm_csf','global_signal']:
                raise ValueError(
                    f'{k} not a valid noise component to include!\n'
                    f'If {k} is a valid parameter in '
                    'nilearn.interfaces.fmriprep.load_confounds we may '
                    'include it in the future'
                )
            if v not in ['basic','power2','derivatives','full']:
                raise ValueError(
                    f'{v} not a valid type of confound to extract from input '
                    'signal!'
                )


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

    def read_confounds(self):
        raise NotImplementedError('read_confounds not implemented')

    def remove_confounds(self):
        pass

    def fit_transform(self, input):
        out = {}
        meta = input.get('meta', {})
        bold_img = input['BOLD']['data']
        confounds_df = input['confounds']
        selected_confounds = self.read_confounds(confounds_df)
        clean_img = self.remove_confounds(bold_img, confounds_df)


        return out

class FelixConfoundRemover(BaseConfoundRemover):

    def read_confounds(self, confound_dataframe):
        
        confounds_to_select = []
        # for some confounds we need to manually calculate derivatives using
        # numpy and add them to the output
        derivatives_to_calculate = []

        for comp, param in self.strategy.items():
            if comp == 'motion':

                # there should be six rigid body parameters                
                for i in range(1,7):
                    # select basic
                    confounds_to_select.append(f'RP.{i}')
                    
                    # select squares 
                    if param in ['power2', 'full']:
                        confounds_to_select.append(f'RP^2.{i}')
                    
                    # select derivatives
                    if param in ['derivatives', 'full']:
                        confounds_to_select.append(f'DRP.{i}')
                    
                    # if 'full' we should not forget the derivative 
                    # of the squares
                    if param in ['full']:
                        confounds_to_select.append(f'DRP^2.{i}')

            elif comp == 'wm_csf':
                confounds = ['WM', 'CSF']
            elif comp == 'global_signal':
                confounds = ['GS']
            
            for conf in confounds:

                confounds_to_select.append(conf)
                    
                # select squares
                if param in ['power2', 'full']:
                    confounds_to_select.append(f'{conf}^2')

                # we have to calculate derivatives (not included in felix'
                # confound files)
                if param in ['derivatives', 'full']:
                    derivatives_to_calculate.append(conf)
                    
                if param in ['full']:
                    derivatives_to_calculate.append(f'{conf}^2')

        confounds_to_remove = confound_dataframe[confounds_to_select]
        
        for conf in derivatives_to_calculate:
            confounds_to_remove[f'D{conf}'] = np.append(
                np.diff(confound_dataframe[conf]), 0
            )

        return confounds_to_remove

class FmriprepConfoundRemover(BaseConfoundRemover):
    """ A ConfoundRemover class for fmriprep output utilising
    nilearn's nilearn.interfaces.fmriprep.load_confounds
    """

    def read_confounds(self):
        raise NotImplementedError('read_confounds not implemented')
        