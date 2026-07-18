#!/usr/bin/env python3

# Imports

from functools import partial
from multiprocessing import Pool

import pandas as pd
import statsmodels.formula.api as smf

# Function


def _fit_bootstrap_sample(df: pd.DataFrame, seed: int) -> float:
    # Resample groups with replacement
    bootstrap_sample = df.sample(frac=1, replace=True, random_state=seed)

    # Fit the model on the bootstrap sample
    mod_win_props = smf.mixedlm(
        formula="Proportions ~ 1 + AvgChange + NumMatches",
        data=bootstrap_sample,
        groups="Bookies",
        re_formula="1 + AvgChange",
    )

    res_mod_win_props = mod_win_props.fit(reml=False, method="lbfgs")

    return res_mod_win_props.params["AvgChange"]


def bootstrap_std_error(
    df: pd.DataFrame, n_bootstraps: int, seed: int
) -> pd.DataFrame:
    """
    Bootstrap standard error.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    n_bootstraps : int
        Number of bootstrap samples.
    seed : int
        Random seed. Each bootstrap sample gets its own deterministic
        seed derived from this (seed + sample index), since the
        samples are drawn in parallel and so can't share one
        sequentially-advancing random stream.

    Returns
    -------
    pd.DataFrame
        DataFrame containing bootstrap coefficients.

    """
    part_fit_bootstrap_sample = partial(_fit_bootstrap_sample, df)

    with Pool() as pool:
        bootstrap_coefs = pool.map(
            part_fit_bootstrap_sample,
            [seed + i for i in range(n_bootstraps)],
        )

    # Convert list of coefficients to a DataFrame
    bootstrap_coefs_df = pd.DataFrame(bootstrap_coefs)

    return bootstrap_coefs_df
