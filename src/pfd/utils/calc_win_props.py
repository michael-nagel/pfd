#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import numpy as np
import pandas as pd
from scipy.stats import norm

# Function


def calc_win_props(df: pd.DataFrame, ival: list) -> list:
    """
    Calculate the elapsed time of a time-series.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    ival : list
        List indicating the interval.

    Returns
    -------
    list
        List containing various metrics.

    """
    if all(x <= 0 for x in ival):
        df = df.loc[
            (df["DltOpnCls"] >= ival[0]) & (df["DltOpnCls"] < ival[1])
        ].copy()
    elif all(x >= 0 for x in ival):
        df = df.loc[
            (df["DltOpnCls"] > ival[0]) & (df["DltOpnCls"] <= ival[1])
        ].copy()
    else:
        raise ValueError("Invalid interval: {}".format(ival))

    n_matches = df.shape[0]
    win_prop = df["Match"].mean()
    z_stat = (win_prop - 0.5) / (df["Match"].std() / np.sqrt(n_matches))
    p_val = 2 * (1 - norm.cdf(x=np.abs(z_stat), loc=0, scale=1))
    avg_chg = df["DltOpnCls"].mean()
    num_odds_mvt = df["NumOddsMvt"].mean()

    return [ival, avg_chg, num_odds_mvt, n_matches, win_prop, z_stat, p_val]
