#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

from pfd.utils import enc_categ_var

# Function


def impute_missings(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """
    Impute missing values.

    This function imputes missings values using sklearn's iterative
    imputer.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    seed: int
        Random seed.

    Returns
    -------
    pd.DataFrame
        Imputed DataFrame.
    """

    imputer = IterativeImputer(
        initial_strategy="median", min_value=0, max_value=1, random_state=seed
    )

    df = enc_categ_var(
        df=df,
        col="Bookies",
        prefix="Bookie",
        rm_first=True,
        rm_categ_var=False,
    )

    df.loc[:, df.columns != "Bookies"] = imputer.fit_transform(
        X=df.loc[:, df.columns != "Bookies"]
    )

    df = df.drop(
        labels=[col for col in df.columns if col.startswith("Bookie_")], axis=1
    )

    return df
