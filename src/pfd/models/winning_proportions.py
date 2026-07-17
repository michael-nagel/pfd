#!/usr/bin/env python3

"""
This file analyzes the magnitude and direction of odds movements.
"""

# Imports

from collections import defaultdict
from typing import Any

import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scipy.stats import norm

from pfd.utils import (
    PFDConfig,
    PlotParams,
    bootstrap_std_error,
    calc_win_props,
    finalize_plot,
)

# Function


def analyze_winning_proportions(
    df_oc: pd.DataFrame,
    bookies: list[str],
    cfg: PFDConfig,
    plot_params: PlotParams,
    stata_colors: list,
) -> tuple[dict[str, pd.DataFrame], list[str], pd.Series, pd.Series, pd.Series]:
    """
    Analyze the magnitude and direction of odds movements.

    This function calculates the winning proportions within intervals
    of opening-to-closing price changes, and estimates the relation
    between winning rates and the average price movements within
    those intervals.

    Parameters
    ----------
    df_oc : pd.DataFrame
        DataFrame with one row per group (first observation), as
        produced by analyze_bookmaker_accuracy().
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
        res_win_props, tex_res_wp_re, bootstr_std, bootstr_low,
        bootstr_up.
    """
    # Magnitude and Direction of Odds Movements

    # Calculate the difference in opening and closing odds
    df_oc["DltOpnCls"] = df_oc["ClsOdds"] - df_oc["OpnOdds"]

    # Calculate the winning proportions within different intervals
    res_win_props: defaultdict[Any, list] = defaultdict(list)

    ivals = [
        [-1, -0.15],
        [-0.15, -0.12],
        [-0.12, -0.09],
        [-0.09, -0.06],
        [-0.06, -0.03],
        [-0.03, 0],
        [0, 0.03],
        [0.03, 0.06],
        [0.06, 0.09],
        [0.09, 0.12],
        [0.12, 0.15],
        [0.15, 1],
    ]

    for bookie in bookies + ["All"]:
        if bookie == "All":
            for ival in ivals:
                res_win_props["All"].append(calc_win_props(df=df_oc, ival=ival))
        else:
            for ival in ivals:
                res_win_props[bookie].append(
                    calc_win_props(
                        df=df_oc.loc[df_oc["Bookies"] == bookie, :], ival=ival
                    )
                )

    for bookie in bookies + ["All"]:
        res_win_props[bookie] = pd.DataFrame(
            data=res_win_props[bookie],
            columns=[
                "Delta",
                "AvgChange",
                "AvgNumChanges",
                "NumMatches",
                "Proportions",
                "Z-statistic",
                "p-value",
            ],
        )

    # Tests Based on Proportions

    # Estimate the relation between winning rates and the average odds
    # movements within the intervals defined above
    df_res_win_props = pd.concat(res_win_props, ignore_index=True)

    df_res_win_props["Bookies"] = np.repeat(
        a=list(res_win_props.keys()),
        repeats=res_win_props[bookies[0]].shape[0],
    )

    mod_win_props = smf.mixedlm(
        formula="Proportions ~ 1 + AvgChange + NumMatches",
        data=df_res_win_props,
        groups="Bookies",
        re_formula="1 + AvgChange",
    )

    res_mod_win_props = mod_win_props.fit(reml=False, method="lbfgs")

    # Plot the estimated random intercepts and slopes
    fixed_effects = res_mod_win_props.fe_params
    random_effects = res_mod_win_props.random_effects

    # Bootstap to obtain correct standard error
    bootstr_coefs = bootstrap_std_error(df=df_res_win_props, n_bootstraps=1000)
    bootstr_std = bootstr_coefs.std()
    bootstr_low = fixed_effects["AvgChange"] - norm.ppf(0.975) * bootstr_std
    bootstr_up = fixed_effects["AvgChange"] + norm.ppf(0.975) * bootstr_std

    group_params = []
    for group, re in random_effects.items():
        intercept = fixed_effects["Intercept"] + re["Bookies"]
        slope = fixed_effects["AvgChange"] + re["AvgChange"]
        group_params.append(
            {"Bookies": group, "Intercept": intercept, "Slope": slope}
        )

    df_group_params = pd.DataFrame(group_params)

    df_group_params = df_group_params[df_group_params["Bookies"] != "All"]
    df_res_win_props = df_res_win_props[df_res_win_props["Bookies"] != "All"]

    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_small", fig_size=(6.4, 4.8))
    )

    _, ax = plt.subplots()
    sns.scatterplot(
        data=df_res_win_props.loc[df_res_win_props["Bookies"] != "All"],
        x="AvgChange",
        y="Proportions",
        hue="Bookies",
        palette=stata_colors[0 : len(bookies)],
        legend=False,
        ax=ax,
    )
    for _, row in df_group_params.iterrows():
        x = np.linspace(
            df_res_win_props["AvgChange"].min(),
            df_res_win_props["AvgChange"].max(),
            100,
        )
        y = row["Intercept"] + row["Slope"] * x
        ax.plot(x, y, label=row["Bookies"])
    ax.set(xlabel="Average Price Change Magnitude", ylabel="Winning Rate")
    finalize_plot(
        path=f"{cfg.paths.figures}win_props_re.pdf",
        save=cfg.general.save,
    )

    # Create a separate legend figure
    fig_legend, ax_legend = plt.subplots(figsize=(4, 4.5))
    ax_legend.legend(
        *ax.get_legend_handles_labels(),
        loc="center",
        ncol=2,
        # fontsize=9,
        columnspacing=0.4,
        handlelength=1.5,
    )
    ax_legend.axis("off")
    finalize_plot(
        path=f"{cfg.paths.figures}legend.pdf",
        save=cfg.general.save,
    )

    # Replace wrong std. error with bootstrap std. error and store as tex
    tex_res_wp_re = res_mod_win_props.summary().as_latex().splitlines(True)
    tex_res_wp_re = tex_res_wp_re[19:-5]
    tex_res_wp_re.append("\\bottomrule\n")
    tex_res_wp_re[1] = "\\midrule\n"
    tex_res_wp_re[3] = (
        tex_res_wp_re[3][:38]
        + str(bootstr_std[0].round(3))
        + tex_res_wp_re[3][43:-19]
        + str(bootstr_low[0].round(3))
        + tex_res_wp_re[3][-14:-10]
        + str(bootstr_up[0].round(3))
        + tex_res_wp_re[3][-5:]
    )

    for bookie in bookies + ["All"]:
        res_win_props[bookie].rename(
            columns=dict(
                zip(
                    res_win_props[bookie].columns,
                    [
                        "Interval",
                        "Avg. Change",
                        "Avg. Moves",
                        "No. Matches",
                        "Winning Rate",
                        "Z-statistic",
                        "p-value",
                    ],
                    strict=True,
                )
            ),
            inplace=True,
        )

        res_win_props[bookie]["Interval"] = res_win_props[bookie][
            "Interval"
        ].map(lambda x: "$" + str(x) + "$")
        res_win_props[bookie].loc[0:6, "Interval"] = (
            res_win_props[bookie]
            .loc[0:6, "Interval"]
            .str.replace("$[", "$]", regex=False)
        )
        res_win_props[bookie].loc[5::, "Interval"] = (
            res_win_props[bookie]
            .loc[5::, "Interval"]
            .str.replace("]$", "[$", regex=False)
        )

    return res_win_props, tex_res_wp_re, bootstr_std, bootstr_low, bootstr_up
