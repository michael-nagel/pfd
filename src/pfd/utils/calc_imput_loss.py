#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from typing import Callable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

# Function


def calc_imput_loss(
    df: pd.DataFrame,
    odds_mvt_cols: List[str],
    n_mvt: int,
    pctl: int,
    seed: int,
    imp_func: Callable[[pd.DataFrame, int], pd.DataFrame],
) -> List[float]:
    """
    Calculate imputation loss.

    Calcuate the loss implied by the different imputation strategies
    median, linear extrapolating, and mutliple imputation.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    odds_mvt_cols : list
        Columns containing odds movements.
    n_mvt : int
        Number of initially missing columns.
    pctl : int
        Percentile of number of odds movements.
    seed : int
        Random seed.
    imp_func : Callable
        Imputation function.

    Returns
    -------
    list
        Metrics.
    """

    df_imp = df.loc[
        (df.loc[:, odds_mvt_cols[:n_mvt]].notna().all(axis=1))
        & (df["NumOddsMvt"] > df["NumOddsMvt"].quantile(pctl / 100)),
        :,
    ].copy()

    random_rows = df_imp.sample(n=int(1 * df_imp.shape[0]), random_state=seed)
    labels = df_imp.loc[random_rows.index, odds_mvt_cols[:n_mvt]].copy()
    df_imp.loc[random_rows.index, odds_mvt_cols[:n_mvt]] = np.nan

    # Median imputation strategy
    imp_med = df_imp.loc[random_rows.index, odds_mvt_cols].apply(
        lambda row: row.fillna(row.median()), axis=1
    )
    mse_med = mean_squared_error(
        labels, imp_med[odds_mvt_cols[:n_mvt]], squared=False
    )

    # Linear extrapolation strategy
    def lin_extrapol(df):
        coefs = np.polyfit(
            np.arange(n_mvt, len(odds_mvt_cols)),
            df[n_mvt:],
            1,
        )
        vals = np.polyval(coefs, np.arange(0, n_mvt))
        df[0 : len(vals)] = vals
        return df

    imp_lin = df_imp.loc[random_rows.index, odds_mvt_cols].apply(
        lin_extrapol, axis=1
    )
    mse_lin = mean_squared_error(
        labels, imp_lin[odds_mvt_cols[:n_mvt]], squared=False
    )

    # Multiple imputation strategy
    df_imp_mul = df.copy()
    df_imp_mul.loc[random_rows.index, odds_mvt_cols[0:n_mvt]] = np.nan
    df_imp_mul = imp_func(df=df_imp_mul, seed=seed)
    mse_mul = mean_squared_error(
        labels,
        df_imp_mul.loc[random_rows.index, odds_mvt_cols[0:n_mvt]],
        squared=False,
    )

    return [mse_med, mse_lin, mse_mul]
