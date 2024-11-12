"""Provide JuniferConnectivityMeasure class."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Callable, Optional

import numpy as np
from nilearn import signal
from nilearn.connectome import (
    ConnectivityMeasure,
    cov_to_corr,
    prec_to_partial,
    sym_matrix_to_vec,
)
from scipy import linalg, stats
from sklearn.base import clone
from sklearn.covariance import EmpiricalCovariance

from ...utils import logger, raise_error, warn_with_log


__all__ = ["JuniferConnectivityMeasure"]


DEFAULT_COV_ESTIMATOR = EmpiricalCovariance(store_precision=False)


# New BSD License

# Copyright (c) The nilearn developers.
# All rights reserved.


# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#   a. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   b. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#   c. Neither the name of the nilearn developers nor the names of
#      its contributors may be used to endorse or promote products
#      derived from this software without specific prior written
#      permission.


# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.


def _check_square(matrix: np.ndarray) -> None:
    """Raise a ValueError if the input matrix is square.

    Parameters
    ----------
    matrix : numpy.ndarray
        Input array.

    Raises
    ------
    ValueError
        If ``matrix`` is not a square matrix.

    """
    if matrix.ndim != 2 or (matrix.shape[0] != matrix.shape[-1]):
        raise_error(
            f"Expected a square matrix, got array of shape {matrix.shape}."
        )


def is_spd(M: np.ndarray, decimal: int = 15) -> bool:  # noqa: N803
    """Check that input matrix is symmetric positive definite.

    ``M`` must be symmetric down to specified ``decimal`` places.
    The check is performed by checking that all eigenvalues are positive.

    Parameters
    ----------
    M : numpy.ndarray
        Input matrix to check for symmetric positive definite.
    decimal : int, optional
        Decimal places to check (default 15).

    Returns
    -------
    bool
        True if matrix is symmetric positive definite, False otherwise.

    """
    if not np.allclose(M, M.T, atol=0, rtol=10**-decimal):
        logger.debug(f"matrix not symmetric to {decimal:d} decimals")
        return False
    eigvalsh = np.linalg.eigvalsh(M)
    ispd = eigvalsh.min() > 0
    if not ispd:
        logger.debug(f"matrix has a negative eigenvalue: {eigvalsh.min():.3f}")
    return ispd


def _check_spd(matrix: np.ndarray) -> None:
    """Check ``matrix`` is symmetric positive definite.

    Parameters
    ----------
    matrix : numpy.ndarray
        Input array.

    Raises
    ------
    ValueError
        If the input matrix is not symmetric positive definite.

    """
    if not is_spd(matrix, decimal=7):
        raise_error("Expected a symmetric positive definite matrix.")


def _form_symmetric(
    function: Callable[[np.ndarray], np.ndarray],
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
) -> np.ndarray:
    """Return the symmetric matrix.

    Apply ``function`` to ``eigenvalues``, construct symmetric matrix with it
    and ``eigenvectors`` and return the constructed symmetric matrix.

    Parameters
    ----------
    function : callable (function numpy.ndarray -> numpy.ndarray)
        The transform to apply to the eigenvalues.
    eigenvalues : numpy.ndarray of shape (n_features, )
        Input argument of the function.
    eigenvectors : numpy.ndarray of shape (n_features, n_features)
        Unitary matrix.

    Returns
    -------
    numpy.ndarray of shape (n_features, n_features)
        The symmetric matrix obtained after transforming the eigenvalues, while
        keeping the same eigenvectors.

    """
    return np.dot(eigenvectors * function(eigenvalues), eigenvectors.T)


def _map_eigenvalues(
    function: Callable[[np.ndarray], np.ndarray], symmetric: np.ndarray
) -> np.ndarray:
    """Matrix function, for real symmetric matrices.

    The function is applied to the eigenvalues of ``symmetric``.

    Parameters
    ----------
    function : callable (function numpy.ndarray -> numpy.ndarray)
        The transform to apply to the eigenvalues.
    symmetric : numpy.ndarray of shape (n_features, n_features)
        The input symmetric matrix.

    Returns
    -------
    numpy.ndarray of shape (n_features, n_features)
        The new symmetric matrix obtained after transforming the eigenvalues,
        while keeping the same eigenvectors.

    Notes
    -----
    If input matrix is not real symmetric, no error is reported but result will
    be wrong.

    """
    eigenvalues, eigenvectors = linalg.eigh(symmetric)
    return _form_symmetric(function, eigenvalues, eigenvectors)


def _geometric_mean(
    matrices: list[np.ndarray],
    init: Optional[np.ndarray] = None,
    max_iter: int = 10,
    tol: Optional[float] = 1e-7,
) -> np.ndarray:
    """Compute the geometric mean of symmetric positive definite matrices.

    The geometric mean of ``n`` positive definite matrices
    ``M_1, ..., M_n`` is the minimizer of the sum of squared distances from an
    arbitrary matrix to each input matrix ``M_k``

    .. math:: gmean(M_1, ..., M_n) = argmin_X sum_{k=1}^N dist(X, M_k)^2

    where the used distance is related to matrices logarithm

    .. math:: dist(X, M_k) = ||log(X^{-1/2} M_k X^{-1/2)}||

    In case of positive numbers, this mean is the usual geometric mean.

    See Algorithm 3 of [1]_ .

    Parameters
    ----------
    matrices : list of numpy.ndarray, all of shape (n_features, n_features)
        List of matrices whose geometric mean to compute. Raise an error if the
        matrices are not all symmetric positive definite of the same shape.
    init : numpy.ndarray of shape (n_features, n_features), optional
        Initialization matrix, default to the arithmetic mean of matrices.
        Raise an error if the matrix is not symmetric positive definite of the
        same shape as the elements of matrices (default None).
    max_iter : int, optional
        Maximal number of iterations (default 10).
    tol : positive float or None, optional
        The tolerance to declare convergence: if the gradient norm goes below
        this value, the gradient descent is stopped. If None, no check is
        performed (default 1e-7).

    Returns
    -------
    gmean : numpy.ndarray of shape (n_features, n_features)
        Geometric mean of the matrices.

    References
    ----------
    .. [1] Fletcher, T., P., Joshi, S.
           Riemannian geometry for the statistical analysis of diffusion tensor
           data.
           Signal Processing, Volume 87, Issue 2, 2007, Pages 250-262
           https://doi.org/10.1016/j.sigpro.2005.12.018.

    """
    # Shape and symmetry positive definiteness checks
    n_features = matrices[0].shape[0]
    for matrix in matrices:
        _check_square(matrix)
        if matrix.shape[0] != n_features:
            raise_error("Matrices are not of the same shape.")
        _check_spd(matrix)

    # Initialization
    matrices = np.array(matrices)
    if init is None:
        gmean = np.mean(matrices, axis=0)
    else:
        _check_square(init)
        if init.shape[0] != n_features:
            raise_error("Initialization has incorrect shape.")
        _check_spd(init)
        gmean = init

    norm_old = np.inf
    step = 1.0

    # Gradient descent
    for _ in range(max_iter):
        # Computation of the gradient
        vals_gmean, vecs_gmean = linalg.eigh(gmean)
        gmean_inv_sqrt = _form_symmetric(np.sqrt, 1.0 / vals_gmean, vecs_gmean)
        whitened_matrices = [
            gmean_inv_sqrt.dot(matrix).dot(gmean_inv_sqrt)
            for matrix in matrices
        ]
        logs = [_map_eigenvalues(np.log, w_mat) for w_mat in whitened_matrices]
        # Covariant derivative is - gmean.dot(logms_mean)
        logs_mean = np.mean(logs, axis=0)
        if np.any(np.isnan(logs_mean)):
            raise_error(
                klass=FloatingPointError,
                msg="Nan value after logarithm operation.",
            )

        # Norm of the covariant derivative on the tangent space at point gmean
        norm = np.linalg.norm(logs_mean)

        # Update of the minimizer
        vals_log, vecs_log = linalg.eigh(logs_mean)
        gmean_sqrt = _form_symmetric(np.sqrt, vals_gmean, vecs_gmean)
        # Move along the geodesic
        gmean = gmean_sqrt.dot(
            _form_symmetric(np.exp, vals_log * step, vecs_log)
        ).dot(gmean_sqrt)

        # Update the norm and the step size
        if norm < norm_old:
            norm_old = norm
        elif norm > norm_old:
            step = step / 2.0
            norm = norm_old
        if tol is not None and norm / gmean.size < tol:
            break
    if tol is not None and norm / gmean.size >= tol:
        warn_with_log(
            f"Maximum number of iterations {max_iter} reached without "
            f"getting to the requested tolerance level {tol}."
        )

    return gmean


class JuniferConnectivityMeasure(ConnectivityMeasure):
    """Class for custom ConnectivityMeasure.

    Differs from :class:`nilearn.connectome.ConnectivityMeasure` in the
    following ways:

    * default ``cov_estimator`` is
      :class:`sklearn.covariance.EmpiricalCovariance`
    * default ``kind`` is ``"correlation"``
    * supports Spearman's correlation via ``kind="spearman correlation"``

    Parameters
    ----------
    cov_estimator : estimator object, optional
        The covariance estimator
        (default ``EmpiricalCovariance(store_precision=False)``).
    kind : {"covariance", "correlation", "spearman correlation", \
            "partial correlation", "tangent", "precision"}, optional
        The matrix kind. The default value uses Pearson's correlation.
        If ``"spearman correlation"`` is used, the data will be ranked before
        estimating the covariance. For the use of ``"tangent"`` see [1]_
        (default "correlation").
    vectorize : bool, optional
        If True, connectivity matrices are reshaped into 1D arrays and only
        their flattened lower triangular parts are returned (default False).
    discard_diagonal : bool, optional
        If True, vectorized connectivity coefficients do not include the
        matrices diagonal elements. Used only when vectorize is set to True
        (default False).
    standardize : bool, optional
        If standardize is True, the data are centered and normed: their mean
        is put to 0 and their variance is put to 1 in the time dimension
        (default True).

        .. note::

            Added to control passing value to ``standardize`` of
            ``signal.clean`` to call new behavior since passing ``"zscore"`` or
            True (default) is deprecated. This parameter will be deprecated in
            version 0.13 and removed in version 0.15.

    Attributes
    ----------
    cov_estimator_ : estimator object
        A new covariance estimator with the same parameters as
        ``cov_estimator``.
    mean_ : numpy.ndarray
        The mean connectivity matrix across subjects. For ``"tangent"`` kind,
        it is the geometric mean of covariances (a group covariance
        matrix that captures information from both correlation and partial
        correlation matrices). For other values for ``kind``, it is the
        mean of the corresponding matrices.
    whitening_ : numpy.ndarray
        The inverted square-rooted geometric mean of the covariance matrices.

    References
    ----------
    .. [1] Varoquaux, G., Baronnet, F., Kleinschmidt, A. et al.
           Detection of brain functional-connectivity difference in
           post-stroke patients using group-level covariance modeling.
           In Tianzi Jiang, Nassir Navab, Josien P. W. Pluim, and
           Max A. Viergever, editors, Medical image computing and
           computer-assisted intervention - MICCAI 2010, Lecture notes
           in computer science, Pages 200-208. Berlin, Heidelberg, 2010.
           Springer.
           doi:10/cn2h9c.

    """

    def __init__(
        self,
        cov_estimator=DEFAULT_COV_ESTIMATOR,
        kind="correlation",
        vectorize=False,
        discard_diagonal=False,
        standardize=True,
    ):
        super().__init__(
            cov_estimator=cov_estimator,
            kind=kind,
            vectorize=vectorize,
            discard_diagonal=discard_diagonal,
            standardize=standardize,
        )

    def _fit_transform(
        self,
        X,  # noqa: N803
        do_transform=False,
        do_fit=False,
        confounds=None,
    ):
        """Avoid duplication of computation."""
        self._check_input(X, confounds=confounds)
        if do_fit:
            self.cov_estimator_ = clone(self.cov_estimator)

        # Compute all the matrices, stored in "connectivities"
        if self.kind in ["correlation", "spearman correlation"]:
            covariances_std = []
            for x in X:
                x = signal.standardize_signal(
                    x,
                    detrend=False,
                    standardize=self.standardize,
                )

                # rank data if spearman correlation
                # before calculating covariance
                if self.kind == "spearman correlation":
                    x = stats.rankdata(x, axis=0)

                covariances_std.append(self.cov_estimator_.fit(x).covariance_)

            connectivities = [cov_to_corr(cov) for cov in covariances_std]
        else:
            covariances = [self.cov_estimator_.fit(x).covariance_ for x in X]
            if self.kind in ("covariance", "tangent"):
                connectivities = covariances
            elif self.kind == "precision":
                connectivities = [linalg.inv(cov) for cov in covariances]
            elif self.kind == "partial correlation":
                connectivities = [
                    prec_to_partial(linalg.inv(cov)) for cov in covariances
                ]
            else:
                allowed_kinds = (
                    "correlation",
                    "partial correlation",
                    "tangent",
                    "covariance",
                    "precision",
                )
                raise_error(
                    f"Allowed connectivity kinds are {allowed_kinds}. "
                    f"Got kind {self.kind}."
                )

        # Store the mean
        if do_fit:
            if self.kind == "tangent":
                self.mean_ = _geometric_mean(
                    covariances, max_iter=30, tol=1e-7
                )
                self.whitening_ = _map_eigenvalues(
                    lambda x: 1.0 / np.sqrt(x), self.mean_
                )
            else:
                self.mean_ = np.mean(connectivities, axis=0)
                # Fight numerical instabilities: make symmetric
                self.mean_ = self.mean_ + self.mean_.T
                self.mean_ *= 0.5

        # Compute the vector we return on transform
        if do_transform:
            if self.kind == "tangent":
                connectivities = [
                    _map_eigenvalues(
                        np.log, self.whitening_.dot(cov).dot(self.whitening_)
                    )
                    for cov in connectivities
                ]

            connectivities = np.array(connectivities)

            if confounds is not None and not self.vectorize:
                error_message = (
                    "'confounds' are provided but vectorize=False. "
                    "Confounds are only cleaned on vectorized matrices "
                    "as second level connectome regression "
                    "but not on symmetric matrices."
                )
                raise_error(error_message)

            if self.vectorize:
                connectivities = sym_matrix_to_vec(
                    connectivities, discard_diagonal=self.discard_diagonal
                )
                if confounds is not None:
                    connectivities = signal.clean(
                        connectivities, confounds=confounds
                    )

        return connectivities
