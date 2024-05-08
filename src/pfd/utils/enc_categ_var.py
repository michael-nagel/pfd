#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import pandas as pd

# Function


def enc_categ_var(
    df: pd.DataFrame, col: str, prefix: str, rm_first: bool, rm_categ_var: bool
) -> pd.DataFrame:
    """
    Encode a categorical variable.

    This function encodes a categorical variable to a one-hot integer
    array and concatenates it to the input DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with variables to be encoded.
    col : str
        Variables to be encoded.
    prefix : str
        String to prepend DataFrame column names.
    rm_first : bool
        Whether to get k-1 dummies out of k categorical levels by
        removing the first level.
    rm_categ_var : bool
        Whether to remove the input categorical variable after encoding.

    Returns
    -------
    pd.DataFrame
        DataFrame with encoded variables.

    Examples
    --------
    for ele in df.select_dtypes(include=["category"]).columns:
        df = enc_categ_var(df, ele, "_", True, True)
    """
    df = pd.concat(
        [
            df,
            pd.get_dummies(
                df[col],
                prefix=prefix,
                drop_first=rm_first,
                prefix_sep="_",
                dtype="int",
            ),
        ],
        axis=1,
    )

    if rm_categ_var:
        df = df.drop([col], axis=1)

    colnames = list(df.columns)
    colnames = [colname for colname in colnames if colname.startswith(prefix)]
    new_colnames = [colname.replace(" ", "_") for colname in colnames]
    df = df.rename(columns=dict(zip(colnames, new_colnames)))

    return df
