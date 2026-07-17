#!/usr/bin/env python3

"""
This file resamples the time series and imputes missing prices.
"""

# Imports

import os
from functools import partial
from multiprocessing import Pool

import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pfd.helpers import impute_missings
from pfd.utils import (
    PFDConfig,
    PlotParams,
    calc_imput_loss,
    finalize_plot,
    pivot_df,
    resample,
)

# Functions


def _partition_list(lst: list, n_parts: int) -> list[list]:
    # Calculate the size of each partition
    avg = len(lst) / float(n_parts)
    out = []
    last = 0.0

    while last < len(lst):
        out.append(lst[int(last) : int(last + avg)])
        last += avg

    return out


def _process_group(
    df_sub: pd.DataFrame, period: float | None, freq: str, pctl: float
) -> pd.DataFrame:
    return df_sub.groupby("GroupId").apply(
        resample,
        period=period,
        freq=freq,
        pctls=np.arange(0, 1 + pctl / 100, pctl / 100),
        include_groups=False,
    )


def resample_and_impute_data(
    df: pd.DataFrame,
    exog_cols: list[str],
    cfg: PFDConfig,
    plot_params: PlotParams,
) -> tuple[pd.DataFrame, list[str], int, float]:
    """
    Resample the time series and impute missing initial prices.

    This function resamples each match/bookmaker time series to a
    common percentile-time grid using multiprocessing, reshapes the
    result to wide format, and imputes prices missing due to
    different opening timestamps across bookmakers.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered and shaped estimation sample.
    exog_cols : list[str]
        Exogenous variables.
    cfg : PFDConfig
        Config parameters.
    plot_params : PlotParams
        Plotting parameters.

    Returns
    -------
    tuple
        df (wide, imputed), odds_mvt_cols, n_per, frac_missings.
    """
    # Time Series

    # Determine the first and the last time stamps of odds updates for each
    # match across bookmakers
    df["TsStart"] = df.groupby("Matchup")["Update"].transform("min")
    df["TsEnd"] = df.groupby("Matchup")["Update"].transform("max")

    df = df.set_index("Update")

    # Remove time series with zero variance in odds
    group_std = df.groupby("GroupId")["OddsMvt"].transform("std")
    df = df[group_std > 0]

    # Resample each time series using multiprocessing
    part_process_group = partial(
        _process_group,
        period=cfg.estimation.period,
        freq=cfg.estimation.resample_freq,
        pctl=cfg.estimation.pctl,
    )

    partitions = _partition_list(
        lst=list(df["Matchup"].unique()), n_parts=cfg.sampling.n_cores
    )

    with Pool(processes=os.cpu_count()) as pool:
        res_pool_resample = pool.map(
            part_process_group,
            [
                df.loc[df["Matchup"].isin(partition)]
                for partition in partitions
            ],
        )

    df = pd.concat(res_pool_resample, ignore_index=False)

    df = df.reset_index(level=1, drop=True).reset_index(drop=False)

    # Remove groups with zero odds variance
    group_std = df.groupby("GroupId")["OddsMvt"].transform("std")
    df = df[group_std > 0]

    n_missings = df["OddsMvt"].isna().sum()
    frac_missings = n_missings / df["OddsMvt"].shape[0]

    # Store DataFrame
    df.to_hdf(
        path_or_buf=f"{cfg.paths.data_intrm}data_resampled.h5",
        key="data_resampled",
        mode="w",
    )

    # Enumerate observations per group
    df["CumCount"] = df.groupby("GroupId").cumcount()

    # Calculate the number of periods of the time series
    n_per = int(df.shape[0] / df.groupby("GroupId").ngroups)

    # Create a list of variables enumerating the odds movements
    odds_mvt_cols = [f"OddsMvt{i}" for i in range(0, n_per)]

    # Reshape DataFrame long to wide
    df = pivot_df(
        df=df,
        exog_cols=exog_cols + ["NumOddsMvt", "IsPro", "IsFav", "Match"],
        n_per=n_per,
    )

    # Imputation of Missing Initial Prices
    perc = [25, 50, 75]
    loss = []
    for ele in perc:
        loss.append(
            calc_imput_loss(
                df=df,
                odds_mvt_cols=odds_mvt_cols,
                n_mvt=round(frac_missings * len(odds_mvt_cols)),
                pctl=ele,
                seed=cfg.general.seed,
                imp_func=impute_missings,
            )
        )

    losses = list(map(list, zip(*loss, strict=True)))
    loss_dict = {
        "median": losses[0],
        "linear": losses[1],
        "multiple": losses[2],
    }

    # Plot metrics
    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_small", fig_size=(6.4, 4.8))
    )

    x = np.arange(len(loss_dict))
    width = 0.25
    multiplier = 0

    _, ax = plt.subplots()
    for _i, (key, val) in enumerate(loss_dict.items()):
        offset = width * multiplier
        ax.bar(x + offset, val, width, label=key)
        multiplier += 1
    ax.set(
        xlabel="Percentile Price Movements",
        ylabel="RMSE",
        ylim=[0, max(max(losses)) * 1.25],
    )
    ax.set_xticks(x + width, perc)
    ax.legend(
        loc="upper center",
        ncol=len(loss_dict),
        columnspacing=0.5,
        handletextpad=0.25,
    )
    finalize_plot(
        path=f"{cfg.paths.figures}imput_loss.pdf",
        save=cfg.general.save,
    )

    # Impute missing values induced through different opening timestamps
    df = impute_missings(df=df, seed=cfg.general.seed)

    return df, odds_mvt_cols, n_per, frac_missings
