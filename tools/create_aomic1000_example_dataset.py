# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
# License: AGPL
from tempfile import TemporaryDirectory
from pathlib import Path

import datalad.api as dl

# repo has to be created on gin manually beforehand if not owner
dst = 'git@gin.g-node.org:/juaml/datalad-example-aomic1000.git'

# Use this if you create repo directly when pushing (see below)
# dst_api = 'git@gin.g-node.org'
# org_name = PurePosixPath('juaml')
# repo_basename = PurePosixPath('datalad-example-aomic1000.git')

with TemporaryDirectory() as tmpdir_name:
    tmpdir = Path(tmpdir_name)
    ds = dl.create(tmpdir)  # type: ignore

    base_dir = tmpdir / 'derivatives'
    base_dir.mkdir(exist_ok=True, parents=True)

    for dtype in ['dwipreproc', 'fmriprep']:
        dtype_dir = base_dir / dtype
        dtype_dir.mkdir()

        for i_sub in range(1, 10):
            t_sub = f'sub-{i_sub:04d}'
            sub_dir = dtype_dir / t_sub
            sub_dir.mkdir()

            if dtype == 'fmriprep':
                for dname in ['func', 'anat']:
                    (sub_dir / dname).mkdir()

                fnames = [
                    (f'anat/{t_sub}_space-MNI152NLin2009cAsym_desc-preproc'
                     '_T1w.nii.gz'),
                    (f'anat/{t_sub}_space-MNI152NLin2009cAsym_label-'
                     'CSF_probseg.nii.gz'),
                    (f'anat/{t_sub}_space-MNI152NLin2009cAsym_label-'
                     'GM_probseg.nii.gz'),
                    (f'anat/{t_sub}_space-MNI152NLin2009cAsym_label-'
                     'WM_probseg.nii.gz'),
                    (f'func/{t_sub}_task-moviewatching_space-'
                     'MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'),
                    (f'func/{t_sub}_task-moviewatching_space-'
                     'MNI152NLin2009cAsym_desc-preproc_bold.json'),
                    (f'func/{t_sub}_task-moviewatching_desc-confounds'
                     '_regressors.tsv'),
                    (f'func/{t_sub}_task-moviewatching_desc-confounds'
                     '_regressors.json'),
                ]

            elif dtype == 'dwipreproc':
                dname = 'dwi'
                (sub_dir / dname).mkdir()

                fnames = [
                    (f'{dname}/{t_sub}_desc-preproc_dwi.nii.gz'),
                ]

            for fname in fnames:
                with open(sub_dir / fname, 'w') as f:
                    f.write('placeholder')

    ds.save(recursive=True)
    # use this to create the repo automatically, only possible for juaml owner
    # ds.create_sibling_gin(
    #   (org_name/repo_basename).as_posix(), name='gin', existing='reconfigure',
    #   api=dst_api, access_protocol='ssh')
    ds.siblings('add', name='gin', url=dst)
    ds.push(to='gin', force='all')
