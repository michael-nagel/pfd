#!/usr/bin/env python3

"""
This file analyzes bookmaker accuracy and general price movements.
"""

# Imports

from functools import partial
from multiprocessing import Pool

import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from pfd.helpers import fit_gpm_mod, fit_rfa_mod
from pfd.utils import PFDConfig, PlotParams, calc_rmse, finalize_plot

# Function


def analyze_bookmaker_accuracy(
    df: pd.DataFrame,
    exog_cols: list[str],
    bookies: list[str],
    cfg: PFDConfig,
    plot_params: PlotParams,
    stata_colors: list,
) -> tuple[pd.Series, pd.DataFrame, float, list[str], list[str], pd.DataFrame]:
    """
    Analyze bookmaker accuracy and general price movements.

    This function calculates the accuracy of opening odds across
    bookmakers, general price movements from opening to closing odds,
    and the relative forecast accuracy of opening vs. closing lines.

    Parameters
    ----------
    df : pd.DataFrame
        Filtered and shaped estimation sample.
    exog_cols : list[str]
        Exogenous variables.
    bookies : list[str]
        Bookmakers.
    cfg : PFDConfig
        Config parameters.
    plot_params : PlotParams
        Plotting parameters.
    stata_colors : list
        Color palette.

    Returns
    -------
    tuple
        rmse, df_oc, iqr_rtrns, tex_res_gpm, tex_res_rfa, df_res_rfa.
    """
    # Accuracy of Opening Odds Across Bookmakers

    # Calculate RMSE for each bookmaker
    rmse = df.groupby("Bookies").apply(
        lambda group: calc_rmse(group["Match"], group["OpnOdds"]),
        include_groups=False,
    )

    # Plot metrics using bar plots
    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_big", fig_size=(6.4, 2.8))
    )

    _, ax = plt.subplots()
    sns.barplot(data=rmse, ax=ax)
    ax.set(xlabel="", ylabel="Root Mean Squared Error", ylim=[0.39, 0.49])
    plt.xticks(np.arange(0, len(rmse.index)), rmse.index, rotation=90)
    finalize_plot(path=f"{cfg.paths.figures}rmse.pdf", save=cfg.general.save)

    # General Price Movements

    # Keep first observation of each group
    df_oc = df.groupby("GroupId", as_index=False).first()

    # Caluclate close to end and open to close returns
    df_oc["RtrnClsEnd"] = df_oc["Match"] / df_oc["ClsOdds"] - 1
    df_oc["RtrnOpnCls"] = df_oc["ClsOdds"] / df_oc["OpnOdds"] - 1

    # Keep groups with non-zero open to close returns
    df_oc = df_oc[df_oc["RtrnOpnCls"].abs() > 0]

    # Calculate and plot the inter-quartile range of the open to close returns
    iqr_rtrns = df_oc["RtrnOpnCls"].quantile(0.75) - df_oc[
        "RtrnOpnCls"
    ].quantile(0.25)

    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_small", fig_size=(6.4, 4.8))
    )

    _, ax = plt.subplots()
    sns.histplot(
        data=df_oc,
        x="RtrnOpnCls",
        stat="density",
        fill=True,
        edgecolor=stata_colors[0],
        alpha=1,
    )
    ax.set(xlabel="Return")
    finalize_plot(
        path=f"{cfg.paths.figures}rtrn_opn_cls.pdf",
        save=cfg.general.save,
    )

    # Fit random effects model for general price movements and store as tex
    res_gpm_re = fit_gpm_mod(df=df_oc, exog_cols=exog_cols)

    tex_res_gpm = res_gpm_re.summary().as_latex().splitlines(True)
    tex_res_gpm = tex_res_gpm[19:-5]
    tex_res_gpm.append("\\bottomrule\n")
    tex_res_gpm[1] = "\\midrule\n"

    # Relative Forecast Accuracy of Opening and Closing Lines

    # Calcualte the forecast error implied by opening and closing odds
    df_oc["FEOpn"] = (df_oc["Match"] - df_oc["OpnOdds"]).abs()
    df_oc["FECls"] = (df_oc["Match"] - df_oc["ClsOdds"]).abs()

    # Fit random effects model and store as tex and DataFrame
    part_fit_rfa_mod = partial(fit_rfa_mod, df_oc, exog_cols)

    with Pool() as pool:
        res_rfa = pool.map(part_fit_rfa_mod, bookies + ["All"])

    res_rfa_re = res_rfa[-1]["fitted_model"]

    tex_res_rfa = res_rfa_re.summary().as_latex().splitlines(True)
    tex_res_rfa = tex_res_rfa[19:-5]
    tex_res_rfa.append("\\bottomrule\n")
    tex_res_rfa[1] = "\\midrule\n"

    df_res_rfa = pd.DataFrame(data=res_rfa, index=bookies + ["All"])
    df_res_rfa = df_res_rfa.loc[:, df_res_rfa.columns != "fitted_model"]

    df_res_rfa = df_res_rfa.rename(
        columns=dict(
            zip(
                df_res_rfa.columns,
                [
                    "$N$",
                    "RMSE$(e_0)$",
                    "RMSE$(e_T)$",
                    r"$\beta_0$",
                    r"$\beta_1$",
                    r"$p(\beta_0)$",
                    r"$p(\beta_1)$",
                ],
                strict=True,
            )
        )
    )

    return rmse, df_oc, iqr_rtrns, tex_res_gpm, tex_res_rfa, df_res_rfa
