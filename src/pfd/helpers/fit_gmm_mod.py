# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import chi2
from statsmodels.tools.numdiff import approx_fprime

from pfd.utils import _create_gmm_data, _GenMethMom

# Function


def fit_gmm_mod(
    df: pd.DataFrame,
    n_per: int,
    incr: int,
    start_params: np.ndarray,
    max_iter: int | str,
    bookie: str,
) -> List[Dict[str, float]]:
    """
    Fit GMM model.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    n_per : int
        Number of periods.
    incr : int
        Incremental step for periods.
    start_params : np.ndarray
        Starting values for the parameters to be estimated.
    max_iter : int | str
        Maximum number of iterations.
    bookie : str
        Bookmaker.

    Returns
    -------
    List[Dict[str, float]]
        List of Dictionaries containing various metrics.
    """
    endog, exog, inst = _create_gmm_data(
        df=df.loc[df["Bookies"] == bookie, :], n_per=n_per, incr=incr
    )

    mod_gmm = _GenMethMom(
        endog=endog,
        exog=exog,
        instrument=inst,
        k_moms=14,
        k_params=1,
        n_per=n_per,
    )

    res_tot: List[Dict[str, float]] = []

    for start_params_vals in start_params:
        if max_iter == 1:
            res_gmm = mod_gmm.fit(
                start_params=start_params_vals,
                maxiter=max_iter,
                optim_method="nm",
                has_optimal_weights=False,
                inv_weights=np.eye(N=14),
            )

            moment_conditions = mod_gmm.momcond(res_gmm.params)
            moment_mean = moment_conditions.mean(axis=0)
            # Variance-Covariance Matrix (Omega)
            moment_avar = (
                moment_conditions.T @ moment_conditions / endog.shape[0]
            )

            # Calculate the gradient/Jacobian (G)

            # Helper that returns the vector of 14 mean moments
            def get_mean_moments(params):
                return mod_gmm.momcond(params).mean(axis=0)

            # approx_fprime returns the derivative of the 14 moments w.r.t the params
            # Result should be shape (14,)
            G = approx_fprime(res_gmm.params, get_mean_moments)
            G = G.reshape(14, 1)

            # Weighting Matrix
            W = np.eye(14)

            # Calculate Sandwich Covariance: (G'WG)^-1 G' W Omega W G (G'WG)^-1
            gwg_inv = np.linalg.inv(G.T @ W @ G)

            # Variance of params
            var_params = gwg_inv @ (G.T @ W @ moment_avar @ W @ G) @ gwg_inv

            # Standard Error
            bse = np.sqrt(np.diag(var_params) / endog.shape[0])

            j_stat = (
                endog.shape[0]
                * moment_mean.T
                @ np.linalg.pinv(moment_avar)
                @ moment_mean
            )

            # Degrees of freedom: #moment conditions - #parameters
            degr = 14 - 1

            # Chi-squared test
            p_value = 1 - chi2.cdf(j_stat, degr)

            res_tot.append(
                {
                    "gamma": res_gmm.params[0],
                    "std_gamma": bse[0],
                    "J_stat": j_stat,
                    "p_value": p_value,
                }
            )

        else:
            res_gmm = mod_gmm.fit(
                start_params=start_params_vals,
                maxiter=max_iter,
                optim_method="nm",
            )  # "nm", "bfgs"

            res_tot.append(
                {
                    "gamma": res_gmm.params[0],
                    "std_gamma": res_gmm.bse[0],
                    "J_stat": res_gmm.jtest()[0],
                    "p_value": res_gmm.jtest()[1],
                }
            )

    return res_tot
