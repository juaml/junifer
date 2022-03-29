# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL
import tempfile
import pytest
from pathlib import Path
from junifer.datagrabber.base import (PatternDataGrabber, BaseDataGrabber,
                                      PatternDataladDataGrabber)


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
    elem = dg['elem']
    assert 'meta' in elem
    assert 'datagrabber' in elem['meta']
    assert 'class' in elem['meta']['datagrabber']
    assert MyDataGrabber.__name__ in elem['meta']['datagrabber']['class']

    with pytest.raises(NotImplementedError):
        dg.get_elements()

    with dg:
        assert dg.datadir == Path('/tmp')
        assert dg.types == ['func']


def test_PatternDataGrabber():
    class MyDataGrabber(PatternDataGrabber):
        def get_elements(self):
            return super().get_elements()

    """Test test_PatternDataGrabber"""
    with pytest.raises(TypeError, match=r"types must be a list"):
        MyDataGrabber(datadir='/tmp', types='wrong',
                      patterns=dict(wrong='pattern'),
                      replacements='subject')

    with pytest.raises(TypeError, match=r"must be a list of strings"):
        MyDataGrabber(datadir='/tmp', types=[1, 2, 3],
                      patterns={'1': 'pattern', '2': 'pattern',
                                '3': 'pattern'},
                      replacements='subject')

    with pytest.raises(ValueError, match=r"must have the same length"):
        MyDataGrabber(datadir='/tmp', types=['func', 'anat'],
                      patterns={'1': 'pattern', '2': 'pattern',
                                '3': 'pattern'},
                      replacements=1)

    with pytest.raises(TypeError, match=r"patterns must be a dict"):
        MyDataGrabber(datadir='/tmp', types=['func', 'anat'],
                      patterns='wrong', replacements='subject')

    with pytest.raises(ValueError,
                       match=r"patterns must have the same length"):
        MyDataGrabber(datadir='/tmp', types=['func', 'anat'],
                      patterns={'wrong': 'pattern'}, replacements='subject')

    with pytest.raises(ValueError, match=r"patterns must contain all types"):
        MyDataGrabber(datadir='/tmp', types=['func', 'anat'],
                      patterns={'wrong': 'pattern', 'func': 'pattern'},
                      replacements='subject')

    with pytest.raises(TypeError, match=r"must be a list of strings"):
        MyDataGrabber(datadir='/tmp', types=['func', 'anat'],
                      patterns={'func': 'func/test', 'anat': 'anat/test'},
                      replacements=1)

    with pytest.warns(RuntimeWarning, match=r"not part of any pattern"):
        MyDataGrabber(datadir='/tmp', types=['func', 'anat'],
                      patterns={'func': 'func/{subject}.nii',
                                'anat': 'anat/{subject}.nii'},
                      replacements=['subject', 'wrong'])

    datagrabber = MyDataGrabber(
        datadir='/tmp/data', types=['func', 'anat'],
        patterns={'func': 'func/{subject}.nii',
                  'anat': 'anat/{subject}.nii'},
        replacements='subject')
    assert datagrabber.datadir == Path('/tmp/data')
    assert datagrabber.types == ['func', 'anat']
    assert datagrabber.replacements == ['subject']

    datagrabber = MyDataGrabber(
        datadir=Path('/tmp/data'), types=['func', 'anat'],
        patterns={'func': 'func/{subject}.nii',
                  'anat': 'anat/{subject}_{session}.nii'},
        replacements=['subject', 'session'])
    assert datagrabber.datadir == Path('/tmp/data')
    assert datagrabber.types == ['func', 'anat']
    assert datagrabber.replacements == ['subject', 'session']


def test_bids_datalad_PatternDataGrabber():
    """Test a subject-based BIDS datalad datagrabber"""
    types = ['T1w', 'bold']
    patterns = {
        'T1w': 'anat/{subject}_T1w.nii.gz',
        'bold': 'func/{subject}_task-rest_bold.nii.gz'
    }
    replacements = ['subject']

    class MyDataGrabber(PatternDataladDataGrabber):
        def get_elements(self):
            elems = [x.name for x in self.datadir.iterdir() if x.is_dir()]
            return elems

    with pytest.raises(ValueError, match=r"uri must be provided"):
        MyDataGrabber(datadir=None, types=types, patterns=patterns,
                      replacements=replacements)

    repo_uri =  _testing_dataset['example_bids']['uri']
    rootdir = 'example_bids'
    repo_commit =  _testing_dataset['example_bids']['id']

    with MyDataGrabber(rootdir=rootdir, uri=repo_uri,
                       types=types, patterns=patterns,
                       replacements=replacements) as dg:
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
            assert dg_meta['class'] == 'MyDataGrabber'
            assert 'uri' in dg_meta
            assert dg_meta['uri'] == repo_uri
            assert 'dataset_commit_id' in dg_meta
            assert dg_meta['dataset_commit_id'] == repo_commit

            with open(t_sub['T1w']['path'], 'r') as f:
                assert f.readlines()[0] == 'placeholder'

    with tempfile.TemporaryDirectory() as tmpdir:
        datadir = Path(tmpdir) / 'dataset'  # Need this for testing
        with MyDataGrabber(rootdir=rootdir, uri=repo_uri,
                           types=types, patterns=patterns,
                           datadir=datadir, replacements=replacements) as dg:
            assert dg.datadir == datadir / rootdir
