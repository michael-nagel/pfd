#!/usr/bin/env python3

"""
This file resamples the time series onto a per-series percentile grid.

No imputation happens here any more: the grid of each series runs from that
bookmaker's own opening price to its own closing price, so every cell falls
inside a period during which the bookmaker actually quoted.
"""

# Imports

import os
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd

from pfd.utils import PFDConfig, pivot_df, resample

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
) -> tuple[pd.DataFrame, list[str], int]:
    """
    Resample the time series onto a per-series percentile grid.

    This function resamples each match/bookmaker time series to a
    percentile-time grid spanning that series' own quoting period, using
    multiprocessing, and reshapes the result to wide format.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered and shaped estimation sample.
    exog_cols : list[str]
        Exogenous variables.
    cfg : PFDConfig
        Config parameters.

    Returns
    -------
    tuple
        df (wide), odds_mvt_cols, n_per.
    """
    # Time Series

    # Determine the first and the last time stamps of odds updates for each
    # series, i.e. each bookmaker's own quoting period. Anchoring the grid
    # per series rather than per match is what removes the backward
    # imputation: every grid cell now falls inside a period during which
    # that bookmaker actually quoted a price (Referee 2, Critical Comment 2).
    df["TsStart"] = df.groupby("GroupId")["Update"].transform("min")
    df["TsEnd"] = df.groupby("GroupId")["Update"].transform("max")

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

    # With the grid anchored per series there are no missing cells left to
    # impute; assert it rather than assume it.
    n_missings = int(df["OddsMvt"].isna().sum())
    if n_missings:
        raise ValueError(
            f"{n_missings} missing prices after resampling; with a "
            "series-anchored grid there should be none."
        )

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

    return df, odds_mvt_cols, n_per
