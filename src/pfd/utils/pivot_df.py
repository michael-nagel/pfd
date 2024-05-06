#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import numpy as np
import pandas as pd

# Function


def pivot_df(df: pd.DataFrame, exog_cols: list, n_per: int) -> pd.DataFrame:
    """
    Pivot DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to be reshaped.
    exog_cols: list
        Exogenous variables.
    n_per: int
        Number of periods.

    Returns
    -------
    pd.DataFrame
        Reshaped DataFrame.
    """

    df = pd.pivot_table(
        data=df,
        values="OddsMvt",
        columns="CumCount",
        index=["Matchup", "Bookies"] + exog_cols,
    )

    df = df.reset_index(drop=False)
    df = df.rename(
        columns=dict(
            zip(
                np.arange(0, n_per),
                ["OddsMvt" + str(ele) for ele in np.arange(0, n_per)],
            )
        )
    )

    return df
