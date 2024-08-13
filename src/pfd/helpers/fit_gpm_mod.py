# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import pandas as pd
import statsmodels
import statsmodels.formula.api as smf

from pfd.utils import scale_vars

# Function


def fit_gpm_mod(
    df: pd.DataFrame, exog_cols: list
) -> statsmodels.regression.mixed_linear_model.MixedLMResultsWrapper:
    """
    Fit general price movements model.

    This function fits the model to assess the general price movements.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    exog_cols: list
        Exogenous variables.

    Returns
    -------
    statsmodels.regression.mixed_linear_model.MixedLMResultsWrapper
        Regression output.
    """
    mod_gpm = smf.mixedlm(
        formula="RtrnClsEnd ~ 1 + RtrnOpnCls + TsDur + Compet_Challenger_Men +\
            Compet_ITF_Men + Compet_Misc + Compet_WTA",
        data=df,
        groups="Bookies",
        re_formula="1 + RtrnOpnCls",
    )

    res_gpm = mod_gpm.fit(reml=False, method="lbfgs")

    return res_gpm
