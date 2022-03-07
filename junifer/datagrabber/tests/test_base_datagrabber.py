# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL
import pytest
from pathlib import Path
from junifer.datagrabber.base import BIDSDataGrabber, BIDSDataladDataGrabber, \
    BaseDataGrabber


_testing_dataset = {
    'example_bids': {
        'uri': 'https://gin.g-node.org/juaml/datalad-example-bids',
        'id': 'e2ce149bd723088769a86c72e57eded009258c6b'
    }
}


def test_BaseDataGrabber():
    """Test BaseDataGrabber"""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseDataGrabber(datadir='/tmp', types=['func'])  # type: ignore

    class MyDataGrabber(BaseDataGrabber):
        def __getitem__(self, element):
            return super().__getitem__(element)

        def get_elements(self):
            return super().get_elements()

    dg = MyDataGrabber(datadir='/tmp', types=['func'])
    with pytest.raises(NotImplementedError):
        dg['elem']

    with pytest.raises(NotImplementedError):
        dg.get_elements()


def test_BIDSDataGrabber():
    """Test BIDSDataGrabber"""
    with pytest.raises(TypeError, match=r"types must be a list"):
        BIDSDataGrabber(datadir='/tmp', types='wrong',
                        patterns=dict(wrong='pattern'))

    with pytest.raises(TypeError, match=r"must be a list of strings"):
        BIDSDataGrabber(datadir='/tmp', types=[1, 2, 3],
                        patterns={'1': 'pattern', '2': 'pattern',
                                  '3': 'pattern'})

    datagrabber = BIDSDataGrabber(
        datadir='/tmp/data', types=['func', 'anat'],
        patterns=dict(func='pattern1', anat='pattern2'))
    assert datagrabber.datadir == Path('/tmp/data')
    assert datagrabber.types == ['func', 'anat']

    datagrabber = BIDSDataGrabber(
        datadir=Path('/tmp/data'), types=['func', 'anat'],
        patterns=dict(func='pattern1', anat='pattern2'))
    assert datagrabber.datadir == Path('/tmp/data')
    assert datagrabber.types == ['func', 'anat']

    with pytest.raises(TypeError, match=r"patterns must be a dict"):
        BIDSDataGrabber(datadir='/tmp', types=['func', 'anat'],
                        patterns='wrong')

    with pytest.raises(ValueError,
                       match=r"patterns must have the same length"):
        BIDSDataGrabber(datadir='/tmp', types=['func', 'anat'],
                        patterns={'wrong': 'pattern'})

    with pytest.raises(ValueError, match=r"patterns must contain all types"):
        BIDSDataGrabber(datadir='/tmp', types=['func', 'anat'],
                        patterns={'wrong': 'pattern', 'func': 'pattern'})


def test_BIDSDataladDataGrabber():
    """Test BIDSDataladDataGrabber"""
    types = ['T1w', 'bold']
    patterns = {
        'T1w': 'anat/{subject}_T1w.nii.gz',
        'bold': 'func/{subject}_task-rest_bold.nii.gz'
    }

    with pytest.raises(ValueError, match=r"uri must be provided"):
        BIDSDataladDataGrabber(datadir=None, types=types, patterns=patterns)

    repo_uri =  _testing_dataset['example_bids']['uri']
    rootdir = 'example_bids'
    repo_commit =  _testing_dataset['example_bids']['id']

    with BIDSDataladDataGrabber(rootdir=rootdir, uri=repo_uri,
                                types=types, patterns=patterns) as dg:
        subs = [x for x in dg]
        expected_subs = [f'sub-{i:02d}' for i in range(1, 10)]
        assert set(subs) == set(expected_subs)

        for elem in dg:
            t_sub = dg[elem]
            assert 'path' in t_sub['T1w']
            assert t_sub['T1w']['path'] == \
                (dg.datadir / f'{elem}/anat/{elem}_T1w.nii.gz')
            assert 'path' in t_sub['bold']
            assert t_sub['bold']['path'] == \
                (dg.datadir / f'{elem}/func/{elem}_task-rest_bold.nii.gz')

            assert 'meta' in t_sub
            assert 'datagrabber' in t_sub['meta']
            dg_meta = t_sub['meta']['datagrabber']
            assert 'class' in dg_meta
            assert dg_meta['class'] == 'BIDSDataladDataGrabber'
            assert 'uri' in dg_meta
            assert dg_meta['uri'] == repo_uri
            assert 'dataset_commit_id' in dg_meta
            assert dg_meta['dataset_commit_id'] == repo_commit

            with open(t_sub['T1w']['path'], 'r') as f:
                assert f.readlines()[0] == 'placeholder'
