"""Provide class for BrainPrint."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import uuid
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Union,
)

from ..api.decorators import register_marker
from ..external.BrainPrint.brainprint.brainprint import (
    compute_asymmetry,
    compute_brainprint,
)
from ..external.BrainPrint.brainprint.surfaces import surf_to_vtk
from ..pipeline import WorkDirManager
from ..utils import logger, run_ext_cmd
from .base import BaseMarker


@register_marker
class BrainPrint(BaseMarker):
    """Class for BrainPrint.

    Parameters
    ----------
    num : positive int, optional
        Number of eigenvalues to compute (default 50).
    skip_cortex : bool, optional
        Whether to skip cortical surface or not (default False).
    keep_eigenvectors : bool, optional
        Whether to also return eigenvectors or not (default False).
    norm : str, optional
        Eigenvalues normalization method (default "none").
    reweight : bool, optional
        Whether to reweight eigenvalues or not (default False).
    asymmetry : bool, optional
        Whether to calculate asymmetry between lateral structures
        (default False).
    asymmetry_distance : {"euc"}, optional
        Distance measurement to use if ``asymmetry=True``:

        * ``"euc"`` : Euclidean

        (default "euc").
    use_cholmod : bool, optional
        If True, attempts to use the Cholesky decomposition for improved
        execution speed. Requires the ``scikit-sparse`` library. If it cannot
        be found, an error will be thrown. If False, will use slower LU
        decomposition (default False).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    """

    _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
        {
            "name": "freesurfer",
            "commands": [
                "mri_binarize",
                "mri_pretess",
                "mri_mc",
                "mris_convert",
            ],
        },
    ]

    _DEPENDENCIES: ClassVar[Set[str]] = {"lapy"}

    def __init__(
        self,
        num: int = 50,
        skip_cortex=False,
        keep_eigenvectors: bool = False,
        norm: str = "none",
        reweight: bool = False,
        asymmetry: bool = False,
        asymmetry_distance: str = "euc",
        use_cholmod: bool = False,
        name: Optional[str] = None,
    ) -> None:
        self.num = num
        self.skip_cortex = skip_cortex
        self.keep_eigenvectors = keep_eigenvectors
        self.norm = norm
        self.reweight = reweight
        self.asymmetry = asymmetry
        self.asymmetry_distance = asymmetry_distance
        self.use_cholmod = use_cholmod
        super().__init__(name=name, on="FreeSurfer")

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["FreeSurfer"]

    def get_output_type(self, input_type: str) -> str:
        """Get output type.

        Parameters
        ----------
        input_type : str
            The data type input to the marker.

        Returns
        -------
        str
            The storage type output by the marker.

        """
        return "vector"

    def _create_aseg_surface(
        self,
        aseg_path: Path,
        norm_path: Path,
        indices: List,
    ) -> Path:
        """Generate a surface from the aseg and label files.

        Parameters
        ----------
        aseg_path : pathlib.Path
            The FreeSurfer aseg path.
        norm_path : pathlib.Path
            The FreeSurfer norm path.
        indices : list
            List of label indices to include in the surface generation.

        Returns
        -------
        pathlib.Path
            Path to the generated surface in VTK format.

        """
        tempfile_prefix = f"aseg.{uuid.uuid4}"

        # Set mri_binarize command
        mri_binarize_output_path = self._tempdir / f"{tempfile_prefix}.mgz"
        mri_binarize_cmd = [
            "mri_binarize",
            f"--i {aseg_path.resolve()}",
            f"--match {''.join(indices)}",
            f"--o {mri_binarize_output_path.resolve()}",
        ]
        # Call mri_binarize command
        run_ext_cmd(name="mri_binarize", cmd=mri_binarize_cmd)

        label_value = "1"
        # Fix label (pretess)
        # Set mri_pretess command
        mri_pretess_cmd = [
            "mri_pretess",
            f"{mri_binarize_output_path.resolve()}",
            f"{label_value}",
            f"{norm_path.resolve()}",
            f"{mri_binarize_output_path.resolve()}",
        ]
        # Call mri_pretess command
        run_ext_cmd(name="mri_pretess", cmd=mri_pretess_cmd)

        # Run marching cube to extract surface
        # Set mri_mc command
        mri_mc_output_path = self._tempdir / f"{tempfile_prefix}.surf"
        mri_mc_cmd = [
            "mri_mc",
            f"{mri_binarize_output_path.resolve()}",
            f"{label_value}",
            f"{mri_mc_output_path.resolve()}",
        ]
        # Run mri_mc command
        run_ext_cmd(name="mri_mc", cmd=mri_mc_cmd)

        # Convert to vtk
        # Set mris_convert command
        surface_path = (
            self._element_tempdir / f"aseg.final.{'_'.join(indices)}.vtk"
        )
        mris_convert_cmd = [
            "mris_convert",
            f"{mri_mc_output_path.resolve()}",
            f"{surface_path.resolve()}",
        ]
        # Run mris_convert command
        run_ext_cmd(name="mris_convert", cmd=mris_convert_cmd)

        return surface_path

    def _create_aseg_surfaces(
        self,
        aseg_path: Path,
        norm_path: Path,
    ) -> Dict[str, Path]:
        """Create surfaces from FreeSurfer aseg labels.

        Parameters
        ----------
        aseg_path : pathlib.Path
            The FreeSurfer aseg path.
        norm_path : pathlib.Path
            The FreeSurfer norm path.

        Returns
        -------
        dict
            Dictionary of label names mapped to corresponding surface paths.

        """
        # Define aseg labels

        # combined and individual aseg labels:
        # - Left  Striatum: left  Caudate + Putamen + Accumbens
        # - Right Striatum: right Caudate + Putamen + Accumbens
        # - CorpusCallosum: 5 subregions combined
        # - Cerebellum: brainstem + (left+right) cerebellum WM and GM
        # - Ventricles: (left+right) lat.vent + inf.lat.vent + choroidplexus +
        #               3rdVent + CSF
        # - Lateral-Ventricle: lat.vent + inf.lat.vent + choroidplexus
        # - 3rd-Ventricle: 3rd-Ventricle + CSF

        aseg_labels = {
            "CorpusCallosum": ["251", "252", "253", "254", "255"],
            "Cerebellum": ["7", "8", "16", "46", "47"],
            "Ventricles": ["4", "5", "14", "24", "31", "43", "44", "63"],
            "3rd-Ventricle": ["14", "24"],
            "4th-Ventricle": ["15"],
            "Brain-Stem": ["16"],
            "Left-Striatum": ["11", "12", "26"],
            "Left-Lateral-Ventricle": ["4", "5", "31"],
            "Left-Cerebellum-White-Matter": ["7"],
            "Left-Cerebellum-Cortex": ["8"],
            "Left-Thalamus-Proper": ["10"],
            "Left-Caudate": ["11"],
            "Left-Putamen": ["12"],
            "Left-Pallidum": ["13"],
            "Left-Hippocampus": ["17"],
            "Left-Amygdala": ["18"],
            "Left-Accumbens-area": ["26"],
            "Left-VentralDC": ["28"],
            "Right-Striatum": ["50", "51", "58"],
            "Right-Lateral-Ventricle": ["43", "44", "63"],
            "Right-Cerebellum-White-Matter": ["46"],
            "Right-Cerebellum-Cortex": ["47"],
            "Right-Thalamus-Proper": ["49"],
            "Right-Caudate": ["50"],
            "Right-Putamen": ["51"],
            "Right-Pallidum": ["52"],
            "Right-Hippocampus": ["53"],
            "Right-Amygdala": ["54"],
            "Right-Accumbens-area": ["58"],
            "Right-VentralDC": ["60"],
        }
        return {
            label: self._create_aseg_surface(
                aseg_path=aseg_path,
                norm_path=norm_path,
                indices=indices,
            )
            for label, indices in aseg_labels.items()
        }

    def _create_cortical_surfaces(
        self,
        lh_white_path: Path,
        rh_white_path: Path,
        lh_pial_path: Path,
        rh_pial_path: Path,
    ) -> Dict[str, Path]:
        """Create cortical surfaces from FreeSurfer labels.

        Parameters
        ----------
        lh_white_path : pathlib.Path
            The FreeSurfer lh.white path.
        rh_white_path : pathlib.Path
            The FreeSurfer rh.white path.
        lh_pial_path : pathlib.Path
            The FreeSurfer lh.pial path.
        rh_pial_path : pathlib.Path
            The FreeSurfer rh.pial path.

        Returns
        -------
        dict
            Cortical surface label names with their paths as dictionary.

        """
        return {
            "lh-white-2d": surf_to_vtk(
                lh_white_path.resolve(),
                (self._element_tempdir / "lh.white.vtk").resolve(),
            ),
            "rh-white-2d": surf_to_vtk(
                rh_white_path.resolve(),
                (self._element_tempdir / "rh.white.vtk").resolve(),
            ),
            "lh-pial-2d": surf_to_vtk(
                lh_pial_path.resolve(),
                (self._element_tempdir / "lh.pial.vtk").resolve(),
            ),
            "rh-pial-2d": surf_to_vtk(
                rh_pial_path.resolve(),
                (self._element_tempdir / "rh.pial.vtk").resolve(),
            ),
        }

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict] = None,
    ) -> Dict:
        """Compute.

        Parameters
        ----------
        input : dict
            The FreeSurfer data as dictionary.
        extra_input : dict, optional
            The other fields in the pipeline data object (default None).

        Returns
        -------
        dict
            The computed result as dictionary. The dictionary has the following
            keys:

            * ``eigenvalues`` : dict of surface labels (str) and eigenvalues
                                (``np.ndarray``)
            * ``eigenvectors`` : dict of surface labels (str) and eigenvectors
                                 (``np.ndarray``) if ``keep_eigenvectors=True``
                                 else None
            * ``distances`` : dict of ``{left_label}_{right_label}`` (str) and
                              distance (float) if ``asymmetry=True`` else None

        References
        ----------
        .. [1] Wachinger, C., Golland, P., Kremen, W. et al. (2015)
               BrainPrint: A discriminative characterization of brain
               morphology.
               NeuroImage, Volume 109, Pages 232-248.
               https://doi.org/10.1016/j.neuroimage.2015.01.032.
        .. [2] Reuter, M., Wolter, F.E., Peinecke, N. (2006)
               Laplace-Beltrami spectra as 'Shape-DNA' of surfaces and solids.
               Computer-Aided Design, Volume 38, Issue 4, Pages 342-366.
               https://doi.org/10.1016/j.cad.2005.10.011.

        """
        logger.debug("Computing BrainPrint")

        # Create component-scoped tempdir
        self._tempdir = WorkDirManager().get_tempdir(prefix="brainprint")
        # Create element-scoped tempdir so that the files are
        # available later as nibabel stores file path reference for
        # loading on computation
        self._element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="brainprint"
        )
        # Generate surfaces
        surfaces = self._create_aseg_surfaces(
            aseg_path=input["aseg"]["path"],
            norm_path=input["norm"]["path"],
        )
        if not self.skip_cortex:
            cortical_surfaces = self._create_cortical_surfaces(
                lh_white_path=input["lh_white"]["path"],
                rh_white_path=input["rh_white"]["path"],
                lh_pial_path=input["lh_pial"]["path"],
                rh_pial_path=input["rh_pial"]["path"],
            )
            surfaces.update(cortical_surfaces)
        # Compute brainprint
        eigenvalues, eigenvectors = compute_brainprint(
            surfaces=surfaces,
            keep_eigenvectors=self.keep_eigenvectors,
            num=self.num,
            norm=self.norm,
            reweight=self.reweight,
            use_cholmod=self.use_cholmod,
        )
        # Calculate distances (if required)
        distances = None
        if self.asymmetry:
            distances = compute_asymmetry(
                eigenvalues=eigenvalues,
                distance=self.asymmetry_distance,
                skip_cortex=self.skip_cortex,
            )

        # Delete tempdir
        WorkDirManager().delete_tempdir(self._tempdir)

        return {
            "eigenvalues": eigenvalues,
            "eigenvectors": eigenvectors,
            "distances": distances,
        }
