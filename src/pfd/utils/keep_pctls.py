#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# %% Imports

import numpy as np
import pandas as pd

# %% Function


def keep_pctls(df: pd.DataFrame, pctls: np.ndarray) -> pd.DataFrame:
    """
    Keep percentiles.

    This function selects the values of a column based on the specified
    percentiles/quantiles. For example, read out every 5%-quantile.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    pctls : np.ndarray
        Percentiles.

    Returns
    -------
    pd.DataFrame
        DataFrame.
    """
    return df.loc[
        df["ElapTime"].isin(
            df["ElapTime"].quantile(pctls, interpolation="lower").to_numpy()
        ),
        :,
    ]
