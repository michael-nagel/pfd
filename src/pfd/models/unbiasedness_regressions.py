#!/usr/bin/env python3

"""
This file estimates the unbiasedness regressions.
"""

# Imports

from collections import defaultdict
from functools import partial
from multiprocessing import Pool
from typing import Any

import matplotlib.pylab as pylab
import pandas as pd
from scipy.stats import norm

from pfd.utils import PFDConfig, PlotParams, fit_mixed_lm
from pfd.visualization import plot_unbiased_reg_res

# Function


def estimate_unbiasedness_regressions(
    df: pd.DataFrame,
    odds_mvt_cols: list[str],
    cfg: PFDConfig,
    plot_params: PlotParams,
) -> pd.Index:
    """
    Estimate the unbiasedness regressions.

    This function estimates, for each time increment, whether the
    price at that increment is an unbiased predictor of the match
    outcome, using multiprocessing across time increments.

    Parameters
    ----------
    df : pd.DataFrame
        Wide-format, imputed estimation sample.
    odds_mvt_cols : list[str]
        Columns containing the odds movements.
    cfg : PFDConfig
        Config parameters.
    plot_params : PlotParams
        Plotting parameters.

    Returns
    -------
    pd.Index
        Time increments (in percentiles) at which the price is not a
        significantly biased predictor of the match outcome.
    """
    # Only keep time series with <20 updates
    df_ur = df.loc[df["NumOddsMvt"] < 20, :].copy()

    # Calculate the difference between the odds in all t and the opening odds
    df_ur[odds_mvt_cols[1:]] = df_ur[odds_mvt_cols[1:]].subtract(
        df_ur["OddsMvt0"], axis=0
    )

    # Endogenous variables is defined as the difference between the terminal
    # value and the initial value
    df_ur["Endog"] = df_ur["Match"] - df_ur["OddsMvt0"]

    # Estimate unbiasedness regressions for all t using multiprocessing & plot
    res_ur: defaultdict[Any, list] = defaultdict(list)

    part_fit_mixed_lm = partial(fit_mixed_lm, df_ur)

    with Pool() as pool:
        res_pool_ur = pool.map(part_fit_mixed_lm, odds_mvt_cols[1:])

    for ele in res_pool_ur:
        res_ur["beta_1"].append(ele["beta_1"])
        res_ur["std_beta_1"].append(ele["std_beta_1"])
        res_ur["beta_0"].append(ele["beta_0"])
        res_ur["std_beta_0"].append(ele["std_beta_0"])
        res_ur["rmse"].append(ele["rmse"])

    signific_time_idx = (
        pd.Series(res_ur["beta_1"])
        + norm.ppf(0.975) * pd.Series(res_ur["std_beta_1"])
        > 1
    ) & (
        pd.Series(res_ur["beta_1"])
        - norm.ppf(0.975) * pd.Series(res_ur["std_beta_1"])
        < 1
    )
    signific_time_idx = (
        1 + signific_time_idx[signific_time_idx].index
    ) * cfg.estimation.pctl

    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_big", fig_size=(6.4, 4.8))
    )

    plot_unbiased_reg_res(
        res_ur=res_ur,
        cfg=cfg,
        path=f"{cfg.paths.figures}unbiased_reg.pdf",
        save=cfg.general.save,
    )

    return signific_time_idx
