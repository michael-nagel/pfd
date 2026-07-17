#!/usr/bin/env python3

"""
This file analyzes the statistical properties of the time series data.
"""

# Imports

import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from arch import arch_model
from arch.unitroot import ADF
from matplotlib.ticker import MaxNLocator
from statsmodels.graphics.tsaplots import plot_pacf
from statsmodels.tsa.stattools import pacf

from pfd.utils import PFDConfig, PlotParams, finalize_plot

# Function


def analyze_time_series_diagnostics(
    df: pd.DataFrame,
    exog_cols: list[str],
    odds_mvt_cols: list[str],
    n_per: int,
    cfg: PFDConfig,
    plot_params: PlotParams,
    stata_colors: list,
) -> tuple[float, float, list[str]]:
    """
    Analyze the statistical properties of the resampled time series.

    This function computes cross-sectional (squared) returns, tests
    for stationarity (ADF), inspects the partial autocorrelation
    function, and fits a GARCH model on the significant lags.

    Parameters
    ----------
    df : pd.DataFrame
        Wide-format, imputed estimation sample.
    exog_cols : list[str]
        Exogenous variables.
    odds_mvt_cols : list[str]
        Columns containing the odds movements.
    n_per : int
        Number of periods of the time series.
    cfg : PFDConfig
        Config parameters.
    plot_params : PlotParams
        Plotting parameters.
    stata_colors : list
        Color palette.

    Returns
    -------
    tuple
        adf_stat, adf_p, tex_res_garch.
    """
    # Reshape DataFrame back from wide to long
    df_garch = df.melt(
        id_vars=["Matchup", "Bookies", "NumOddsMvt"] + exog_cols,
        value_name="OddsMvt",
        var_name="CumCount",
        value_vars=odds_mvt_cols,
    )

    # Keep time series with <20 odds updates (Oddsportal provides 20 updates
    # at most such that we cannot be sure whether time series with 20 updates
    # contain all updates)
    df_garch = df_garch.loc[df_garch["NumOddsMvt"] < 20, :]

    # Format data and calculate returns
    df_garch["CumCount"] = df_garch["CumCount"].str.replace(
        pat="OddsMvt", repl=""
    )

    df_garch["CumCount"] = df_garch["CumCount"].astype(int)
    df_garch["GroupId"] = df_garch.groupby(["Matchup", "Bookies"]).ngroup()
    df_garch = df_garch.sort_values(by=["GroupId", "CumCount"])

    def calc_returns(df):
        return df / df.shift() - 1

    df_garch["Return"] = df_garch.groupby("GroupId")["OddsMvt"].transform(
        calc_returns
    )

    # Calculate (squared) cross-sectional returns and plot
    cs_mean_rtrn = df_garch.groupby("CumCount")["Return"].mean().dropna()
    cs_mean_rtrn_sq = cs_mean_rtrn**2

    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_small", fig_size=(6.4, 4.8))
    )

    _, ax = plt.subplots()
    lns_1 = ax.plot(np.arange(1, n_per, 1), cs_mean_rtrn, label="Returns")
    plt.ticklabel_format(axis="y", style="sci", scilimits=(-4, -4))
    ax_2 = ax.twinx()
    lns_2 = ax_2.plot(
        np.arange(1, n_per, 1),
        cs_mean_rtrn_sq,
        color=stata_colors[1],
        label="Sq. Returns",
    )
    ax.set_xlabel("Percentile Time Increments")
    ax.set_ylabel("Mean Returns", labelpad=-3)
    ax_2.set_ylabel("Squared Mean Returns", labelpad=10)
    plt.xticks(
        np.arange(0, n_per, 1)[::5],
        np.arange(0, 100 + cfg.estimation.pctl, cfg.estimation.pctl)[::5],
    )
    lns = lns_1 + lns_2
    labs = [i.get_label() for i in lns]
    ax.legend(lns, labs, loc="center right")
    finalize_plot(
        path=f"{cfg.paths.figures}cs_mean_rtrn.pdf",
        save=cfg.general.save,
    )

    # ADF Test for Stationarity
    adf = ADF(
        y=cs_mean_rtrn, lags=None, trend="ctt", max_lags=None, method="bic"
    )
    adf_stat, adf_p = adf.stat, adf.pvalue

    # Generate partial autocorrelation function and plot
    pacf_values, confint = pacf(
        x=cs_mean_rtrn_sq,
        alpha=0.05,
    )

    signific_idxs = np.where(
        ((confint[:, 0] <= 0) & (confint[:, 1] <= 0))
        | ((confint[:, 0] >= 0) & (confint[:, 1] >= 0))
    )

    garch_lags = signific_idxs[0].max()
    garch_lags = int(max(garch_lags, 1))

    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_big", fig_size=(6.4, 2.8))
    )

    _, ax = plt.subplots(nrows=1, ncols=2, sharey="all")
    plot_pacf(x=cs_mean_rtrn, ax=ax[0], alpha=0.05, markersize=3)
    plot_pacf(x=cs_mean_rtrn_sq, ax=ax[1], alpha=0.05, markersize=3)
    ax[0].set(title="Returns", xlabel="Lags", ylabel="Autocorrelation")
    ax[1].set(title="Sq. Returns", xlabel="Lags", ylabel="")
    ax[0].xaxis.set_major_locator(MaxNLocator(integer=True))
    ax[1].xaxis.set_major_locator(MaxNLocator(integer=True))
    finalize_plot(
        path=f"{cfg.paths.figures}pacf.pdf",
        save=cfg.general.save,
    )

    # Estimate GARCH model using the significant lags from above
    mod_garch = arch_model(
        y=cs_mean_rtrn_sq,
        mean="AR",
        lags=garch_lags,
        vol="EGARCH",
        p=garch_lags,
        o=garch_lags,
        q=garch_lags,
        rescale=True,
    )
    res_garch = mod_garch.fit(cov_type="robust")

    param_rename = {
        "Const": "$\\alpha$",
        "Return[1]": "$\\phi$",
        "omega": "$\\mu$",
        "alpha[1]": "$\\rho$",
        "gamma[1]": "$\\tau$",
        "beta[1]": "$\\psi$",
    }

    tex_res_garch = res_garch.summary().as_latex()
    for original, new in param_rename.items():
        tex_res_garch = tex_res_garch.replace(original, new)
    tex_res_garch = (
        tex_res_garch.replace("\\textbf{", "").replace("}", "").splitlines(True)
    )

    indices = [i for i, x in enumerate(tex_res_garch) if x == "\\bottomrule\n"]
    tex_res_garch_p1 = tex_res_garch[indices[0] + 3 : indices[0] + 7]
    tex_res_garch_p2 = tex_res_garch[indices[0] + 9 : indices[1] + 1]
    tex_res_garch = tex_res_garch_p1 + tex_res_garch_p2

    return adf_stat, adf_p, tex_res_garch
