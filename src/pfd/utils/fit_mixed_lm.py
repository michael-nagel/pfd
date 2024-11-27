# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Function


def fit_mixed_lm(df: pd.DataFrame, exog_var: str) -> dict:
    """
    Fit mixed linear model.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    exog_var : str
        Exogenous variable.

    Returns
    -------
    dict
        Dictionary with various metrics.
    """
    # optimizers = ["nm", "lbfgs" , "cg", "bfgs"]

    df["Exog"] = df[exog_var].copy()

    re_mod = smf.mixedlm(
        formula="Endog ~ 1 + Exog + TsDur + Compet_Challenger_Men +\
              Compet_ITF_Men + Compet_Misc + Compet_WTA",
        data=df,
        groups="Bookies",
        re_formula="1 + Exog",
    )

    # counter = 0
    # converged = False
    # while not converged and counter < len(optimizers) - 1:
    # re_mod_res = re_mod.fit(reml=False, method=optimizers[counter])
    re_mod_res = re_mod.fit(
        reml=False,
        method="lbfgs",
    )  # TODO reml=False, methods=nm works

    # converged = re_mod_res.converged
    # counter += 1

    return {
        # "converged": re_mod_res.converged,
        # "optimizer": optimizers[counter - 1],
        # "res": re_mod_res,
        "beta_1": re_mod_res.fe_params["Exog"],
        "std_beta_1": re_mod_res.bse_fe["Exog"],
        "beta_0": re_mod_res.fe_params["Intercept"],
        "std_beta_0": re_mod_res.bse_fe["Intercept"],
        "rmse": np.sqrt((re_mod_res.resid**2).mean()),
    }
