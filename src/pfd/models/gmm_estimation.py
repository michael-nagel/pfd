#!/usr/bin/env python3

"""
This file estimates the learning rate using GMM.
"""

# Imports

from functools import partial
from multiprocessing import Pool

import matplotlib.pylab as pylab
import numpy as np
import pandas as pd

from pfd.helpers import fit_gmm_mod
from pfd.utils import PFDConfig, PlotParams
from pfd.visualization import plot_gmm_res

# Function


def estimate_gmm_learning_rate(
    df: pd.DataFrame,
    n_per: int,
    bookies: list[str],
    cfg: PFDConfig,
    plot_params: PlotParams,
    stata_colors: list,
) -> tuple[pd.Series, str, str]:
    """
    Estimate the learning rate using GMM.

    This function estimates the bookmaker-specific learning rate using
    continuously updated GMM (CUE) as well as a first-stage GMM
    estimate, both via multiprocessing across bookmakers.

    Parameters
    ----------
    df : pd.DataFrame
        Wide-format, imputed estimation sample.
    n_per : int
        Number of periods of the time series.
    bookies : list[str]
        Bookmakers.
    cfg : PFDConfig
        Config parameters.
    plot_params : PlotParams
        Plotting parameters.
    stata_colors : list
        Color palette.

    Returns
    -------
    tuple
        gamma_stats_gmm, idxmin_gamma_gmm, idxmax_gamma_gmm.
    """
    # Randomly draw 10 starting values for GMM from uniform dist. and fix first
    start_params = list(
        np.array(
            [
                np.random.uniform(low=0, high=1, size=10),
            ]
        ).T
    )
    start_params[0] = np.array([0.01])

    # Estimate the learning rate using GMM (CUE) and multiprocessing
    part_fit_gmm_mod = partial(
        fit_gmm_mod,
        df,
        n_per,
        cfg.estimation.incr,
        start_params,
        cfg.estimation.max_iter,
    )

    with Pool() as pool:
        res_gmm = pool.map(part_fit_gmm_mod, bookies)

    df_res_gmm = pd.DataFrame(data=[ele[0] for ele in res_gmm], index=bookies)

    # Store some estimated values
    gamma_stats_gmm = df_res_gmm["gamma"].agg(["mean", "min", "max"])
    idxmin_gamma_gmm = df_res_gmm["gamma"].idxmin()
    idxmax_gamma_gmm = df_res_gmm["gamma"].idxmax()

    # Estimate the learning rate using first-stage GMM and multiprocessing
    part_fit_gmm_mod_first_stage = partial(
        fit_gmm_mod,
        df,
        n_per,
        cfg.estimation.incr,
        start_params[0],
        1,
    )

    with Pool() as pool:
        res_gmm_first_stage = pool.map(part_fit_gmm_mod_first_stage, bookies)

    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_big", fig_size=(6.4, 4.8))
    )

    plot_gmm_res(
        res_gmm={"first_stage": res_gmm_first_stage, "cue": res_gmm},
        bookies=bookies,
        edgecolor=stata_colors[0],
        paths=[
            f"{cfg.paths.figures}gmm_params.pdf",
            f"{cfg.paths.figures}gmm_jstat.pdf",
            f"{cfg.paths.figures}gmm_pvalue.pdf",
        ],
        save=cfg.general.save,
    )

    return gamma_stats_gmm, idxmin_gamma_gmm, idxmax_gamma_gmm
