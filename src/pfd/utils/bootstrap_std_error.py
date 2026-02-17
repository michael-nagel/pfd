#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import pandas as pd
import statsmodels.formula.api as smf

# Function


def bootstrap_std_error(df: pd.DataFrame, n_bootstraps: int) -> list:
    """
    Bootstrap standard error.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    n_bootstraps : int
        Number of bootstrap samples.

    Returns
    -------
    list
        List containing bootstrap coefficients.

    """

    bootstrap_coefs = []

    for _ in range(n_bootstraps):
        # Resample groups with replacement
        bootstrap_sample = df.sample(frac=1, replace=True)

        # Fit the model on the bootstrap sample
        mod_win_props = smf.mixedlm(
            formula="Proportions ~ 1 + AvgChange + NumMatches",
            data=bootstrap_sample,
            groups="Bookies",
            re_formula="1 + AvgChange",
        )

        res_mod_win_props = mod_win_props.fit(reml=False, method="lbfgs")

        # Store the coefficients
        bootstrap_coefs.append(res_mod_win_props.params["AvgChange"])

    # Convert list of coefficients to a DataFrame
    bootstrap_coefs_df = pd.DataFrame(bootstrap_coefs)

    return bootstrap_coefs_df
