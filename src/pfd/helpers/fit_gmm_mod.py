# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import numpy as np
import pandas as pd
from typing import Dict, List
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
        k_params=2,
        n_per=n_per,
    )

    res_tot: List[Dict[str, float]] = []

    for start_params_vals in start_params:
        res_gmm = mod_gmm.fit(
            start_params=start_params_vals,
            maxiter=max_iter,
            optim_method="nm",
        )  # "nm", "bfgs"

        res_tot.append(
            {
                "gamma": res_gmm.params[0],
                "std_gamma": res_gmm.bse[0],
                "Phi": res_gmm.params[1],
                "std_Phi": res_gmm.bse[1],
                "J_stat": res_gmm.jtest()[0],
                "p_value": res_gmm.jtest()[1],
            }
        )

    return res_tot
