# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path
import tempfile
from numpy.testing import assert_array_equal
import nibabel as nib
from nibabel import testing as nib_testing
import pandas as pd
from pandas.testing import assert_frame_equal

from junifer.datareader import DefaultDataReader


def test_validation():
    """Test validating input/output"""
    kinds = [
        ['T1w', 'BOLD', 'T2', 'dwi'],
        [],
        None,
        ['whatever']
    ]

    reader = DefaultDataReader()

    for t_kind in kinds:
        assert reader.validate_input(t_kind) is None
        assert reader.get_output_kind(t_kind) == t_kind
        assert reader.validate(t_kind) == t_kind


def test_meta():
    """Test reader metadata"""
    reader = DefaultDataReader()
    t_meta = reader.get_meta()
    assert t_meta['class'] == 'DefaultDataReader'

    nib_data_path = Path(nib_testing.data_path)
    t_path = nib_data_path / 'example4d.nii.gz'
    input = {'bold': t_path}
    output = reader.fit_transform(input)
    assert 'meta' in output
    assert 'datareader' in output['meta']
    assert 'class' in output['meta']['datareader']
    assert output['meta']['datareader']['class'] == 'DefaultDataReader'


def test_read_nifti():
    """Test reading NIFTI files"""
    reader = DefaultDataReader()
    nib_data_path = Path(nib_testing.data_path)

    for fname in ['example4d.nii.gz',
                  'reoriented_anat_moved.nii']:
        t_path = nib_data_path / fname

        input = {'bold': t_path}
        output = reader.fit_transform(input)

        assert isinstance(output, dict)
        assert 'bold' in output
        assert isinstance(output['bold'], dict)
        assert 'path' in output['bold']
        assert 'data' in output['bold']

        read_img = output['bold']['data']

        t_read_img = nib.load(t_path)
        assert_array_equal(read_img.get_fdata(), t_read_img.get_fdata())


def test_read_unknown():
    """Test (not) reading unknown files"""
    reader = DefaultDataReader()
    nib_data_path = Path(nib_testing.data_path)

    anat_path = nib_data_path / 'reoriented_anat_moved.nii'
    whatever_path = nib_data_path / 'unexistent.unkwnownextension'

    input = {'anat': anat_path, 'whatever': whatever_path}
    output = reader.fit_transform(input)

    assert isinstance(output, dict)
    assert 'anat' in output
    assert isinstance(output['anat'], dict)
    assert 'path' in output['anat']
    assert isinstance(output['anat']['path'], Path)
    assert 'data' in output['anat']
    assert output['anat']['data'] is not None

    assert isinstance(output['whatever'], dict)
    assert 'path' in output['whatever']
    assert isinstance(output['whatever']['path'], Path)
    assert 'data' in output['whatever']
    assert output['whatever']['data'] is None


def test_read_csv():
    """Test reading CSV files"""
    d = {'col1': [1, 2, 3, 4, 5], 'col2': [3, 4, 5, 6, 7]}
    df = pd.DataFrame(d)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        df.to_csv(tmpdir / 'test.csv')

        reader = DefaultDataReader()
        input = {'csv': tmpdir / 'test.csv'}
        output = reader.fit_transform(input)

        assert isinstance(output, dict)
        assert 'csv' in output
        assert isinstance(output['csv'], dict)
        assert 'path' in output['csv']
        assert 'data' in output['csv']

        read_df = output['csv']['data'][['col1', 'col2']]
        assert_frame_equal(df, read_df)

        df.to_csv(tmpdir / 'test.csv', sep=';')
        input = {'csv': tmpdir / 'test.csv'}
        params = {'csv': {'sep': ';'}}
        output = reader.fit_transform(input, params)

        assert isinstance(output, dict)
        assert 'csv' in output
        assert isinstance(output['csv'], dict)
        assert 'path' in output['csv']
        assert 'data' in output['csv']

        read_df = output['csv']['data'][['col1', 'col2']]
        assert_frame_equal(df, read_df)

        df.to_csv(tmpdir / 'test.tsv', sep='\t')
        input = {'csv': tmpdir / 'test.tsv'}
        output = reader.fit_transform(input)

        assert isinstance(output, dict)
        assert 'csv' in output
        assert isinstance(output['csv'], dict)
        assert 'path' in output['csv']
        assert 'data' in output['csv']

        read_df = output['csv']['data'][['col1', 'col2']]
        assert_frame_equal(df, read_df)
