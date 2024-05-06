# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from pfd.utils import scale_vars

# Function


def fit_rfa_mod(df: pd.DataFrame, exog_cols: list, bookie: str) -> dict:
    """
    Fit relative forecast accuracy model.

    This function fits the model to assess the relative forecast
    accuracy of different bookmakers.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    exog_cols: list
        Exogenous variables.
    bookie : str
        Bookmaker.

    Returns
    -------
    dict
        Dictionary with various metrics.
    """
    if bookie == "All":
        n_matches = df.shape[0]
        rmse_opn = (df["FEOpn"] ** 2).mean() ** 0.5
        rmse_cls = (df["FECls"] ** 2).mean() ** 0.5

        df["Endog"] = df["FEOpn"] - df["FECls"]
        df["FEOpn"] = df["FEOpn"] - df.groupby("Bookies")["FEOpn"].transform(
            "mean"
        )
        df["FECls"] = df["FECls"] - df.groupby("Bookies")["FECls"].transform(
            "mean"
        )
        df["Exog"] = df["FEOpn"] + df["FECls"]

        df["Exog"] = scale_vars(X=df["Exog"].values.reshape(-1, 1))

        mod_rfa = smf.mixedlm(
            formula="Endog ~ 1 + Exog + TsDur + Compet_Challenger_Men + \
                Compet_ITF_Men + Compet_Misc + Compet_WTA",
            data=df,
            groups="Bookies",
            re_formula="1 + Exog",
        )

        res_rfa = mod_rfa.fit(
            reml=True, method="cg"
        )  # ['bfgs', 'lbfgs', 'cg']

    else:
        n_matches = df[df["Bookies"] == bookie].shape[0]
        rmse_opn = (
            df.loc[df["Bookies"] == bookie, "FEOpn"] ** 2
        ).mean() ** 0.5
        rmse_cls = (
            df.loc[df["Bookies"] == bookie, "FECls"] ** 2
        ).mean() ** 0.5

        exog = df.loc[df["Bookies"] == bookie, exog_cols].copy()

        exog["Exog"] = (
            df.loc[df["Bookies"] == bookie, "FEOpn"]
            + df.loc[df["Bookies"] == bookie, "FECls"]
            - (
                df.loc[df["Bookies"] == bookie, "FEOpn"].mean()
                + df.loc[df["Bookies"] == bookie, "FECls"].mean()
            )
        )
        exog = sm.add_constant(exog)

        mod_rfa = sm.OLS(
            endog=df.loc[df["Bookies"] == bookie, "DltOpnCls"], exog=exog
        )
        mod_rfa.exog_names[0] = "Intercept"
        res_rfa = mod_rfa.fit(cov_type="HC1")

    return {
        "fitted_model": res_rfa,
        "n_matches": n_matches,
        "rmse_opn": rmse_opn,
        "rmse_cls": rmse_cls,
        "alpha": res_rfa.params["Intercept"],
        "beta": res_rfa.params["Exog"],
        "p_alpha": res_rfa.pvalues["Intercept"],
        "p_beta": res_rfa.pvalues["Exog"],
    }
