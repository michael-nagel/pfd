#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file runs the estimation procedure.
"""

# Imports

import json
import os
from collections import defaultdict
from functools import partial
from multiprocessing import Pool
from typing import Any, DefaultDict

import arviz as az
import hydra
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from arch import arch_model
from arch.unitroot import ADF
from hydra import compose, initialize
from hydra.core.config_store import ConfigStore
from matplotlib.ticker import MaxNLocator
from scipy.stats import norm
from statsmodels.graphics.tsaplots import plot_pacf
from statsmodels.tsa.stattools import pacf

from pfd.helpers import (
    fit_gmm_mod,
    fit_gpm_mod,
    fit_rfa_mod,
    gen_res_obj,
    impute_missings,
    save_values,
)
from pfd.utils import (
    Logger,
    NumFormat,
    PFDConfig,
    PlotParams,
    calc_win_props,
    create_func_dict,
    enc_categ_var,
    finalize_plot,
    fit_mixed_lm,
    format_sum,
    mod_tex_tab,
    pivot_df,
    resample,
    scale_vars,
    write_text_file,
)
from pfd.visualization import (
    plot_facetgrid,
    plot_gmm_res,
    plot_posteriors,
    plot_traces,
    plot_unbiased_reg_res,
)

# Hydra Setup

cs = ConfigStore.instance()
cs.store(name="pfd_config", node=PFDConfig)

# Function

with initialize(
    version_base=None, config_path="../conf", job_name="run_estimation"
):
    cfg = compose(config_name="config")


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def run_estimation(cfg: PFDConfig) -> None:
    # Logging

    log = Logger.init_logger(name=__name__)
    t_start = Logger.get_time()

    # External Files

    with open(f"{cfg.paths.acc}{cfg.files.clr_plt}", "r") as f:
        stata_colors = json.load(f)

    with open(f"{cfg.paths.acc}{cfg.files.clr_plt_ext}", "r") as f:
        stata_colors_ext = json.load(f)

    stata_colors = stata_colors + stata_colors_ext

    df = pd.read_hdf(
        path_or_buf=f"{cfg.paths.data_proc}shaped_data.h5",
        key=cfg.estimation.spec,
    )

    # Cockpit

    np.random.seed(cfg.general.seed)

    plt.close("all")
    sns.set_theme(palette=stata_colors, style="ticks")

    plot_params = PlotParams(cfg=cfg)
    # 50%, single plots
    rcp_s = plot_params.set_rc_params(kind="fig_small", fig_size=(6.4, 4.8))
    # 75%, 2x1 and 2x2 plots
    rcp_m = plot_params.set_rc_params(kind="fig_medium", fig_size=(6.4, 4.8))
    # 100%, 1x2 plots
    rcp_l = plot_params.set_rc_params(kind="fig_big", fig_size=(6.4, 2.8))

    # Shaping

    # df.Bookies.value_counts()

    n_obs = df.shape[0]

    if cfg.estimation.compets:
        df = df.loc[df["Competition"].isin(cfg.estimation.compets)]

    df["GroupId"] = df.groupby(["Matchup", "Bookies"]).ngroup()

    n_groups = df["GroupId"].nunique()

    df = df[
        df.groupby("Bookies")["Bookies"].transform("size")
        > df["Bookies"].value_counts().quantile(cfg.estimation.bm_quantile)
    ]

    if cfg.estimation.spec == "BmHome":
        df["Match"] = df["Match"] + 1
        df.loc[df["Match"] == 2, "Match"] = 0

    df["TsDur"] = (
        df.groupby("GroupId")["Update"].transform("last")
        - df.groupby("GroupId")["Update"].transform("first")
    ) / np.timedelta64(1, "h")

    df = df[
        (df["TsDur"] >= cfg.estimation.ts_dur[0])
        & (df["TsDur"] <= cfg.estimation.ts_dur[1])
    ]

    df["NumOddsMvt"] = df.groupby("GroupId")["GroupId"].transform("size")
    df["NumOddsMvt"] = df["NumOddsMvt"] - 1

    df["OddsMvt"] = 1 / df["OddsMvt"]

    df = df.assign(
        OpnOdds=df.groupby("GroupId")["OddsMvt"].transform("first"),
        ClsOdds=df.groupby("GroupId")["OddsMvt"].transform("last"),
    )

    bookies = sorted(list(df["Bookies"].unique()))

    df["IsPro"] = 0
    df.loc[df["Competition"].isin(["ATP", "WTA"]), "IsPro"] = 1

    is_amateur, is_pro = df["IsPro"].value_counts(True).tolist()

    df_desc = df.copy()

    df = df[
        [
            "Matchup",
            "GroupId",
            "Competition",
            "IsPro",
            "Bookies",
            "NumOddsMvt",
            "TsDur",
            "Match",
            "Update",
            "OddsMvt",
            "OpnOdds",
            "ClsOdds",
        ]
    ]

    df = enc_categ_var(
        df=df,
        col="Competition",
        prefix="Compet",
        rm_first=True,
        rm_categ_var=True,
    )

    df["TsDur"] = scale_vars(df["TsDur"].to_numpy().reshape(-1, 1))

    exog_cols = [col for col in df.columns if col.startswith("Compet")] + [
        "TsDur"
    ]

    # General Price Movements

    df_oc = df.groupby("GroupId", as_index=False).first()

    df_oc["RtrnOpnCls"] = df_oc["ClsOdds"] / df_oc["OpnOdds"] - 1
    df_oc = df_oc[df_oc["RtrnOpnCls"].abs() > 0]
    iqr_rtrns = df_oc["RtrnOpnCls"].quantile(0.75) - df_oc[
        "RtrnOpnCls"
    ].quantile(0.25)

    pylab.rcParams.update(rcp_s)

    _, ax = plt.subplots()
    sns.histplot(data=df_oc, x="RtrnOpnCls", stat="density")
    ax.set(xlabel="Return")
    finalize_plot(
        path=f"{cfg.paths.figures}rtrn_opn_cls.png",
        save=cfg.general.save,
        fmt="png",
    )

    res_gpm_re = fit_gpm_mod(df=df_oc, exog_cols=exog_cols)

    tex_res_gpm = res_gpm_re.summary().as_latex().splitlines(True)
    tex_res_gpm = tex_res_gpm[19:-5]
    tex_res_gpm.append("\\bottomrule\n")
    tex_res_gpm[1] = "\\midrule\n"

    # Relative Forecast Accuracy of Opening and Closing Lines

    df_oc["FEOpn"] = (df_oc["Match"] - df_oc["OpnOdds"]).abs()
    df_oc["FECls"] = (df_oc["Match"] - df_oc["ClsOdds"]).abs()

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
            )
        )
    )

    # Magnitude and Direction of Odds Movements

    df_oc["DltOpnCls"] = df_oc["ClsOdds"] - df_oc["OpnOdds"]

    res_win_props: DefaultDict[Any, list] = defaultdict(list)

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
                res_win_props["All"].append(
                    calc_win_props(df=df_oc, ival=ival)
                )
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
    # TODO: do also individually using weighted least squares?

    df_res_win_props = pd.concat(res_win_props, ignore_index=True)

    df_res_win_props["Bookies"] = np.repeat(
        a=list(res_win_props.keys()),
        repeats=res_win_props[bookies[0]].shape[0],
    )

    # df_res_win_props[["AvgChange", "NumMatches"]] = scale_vars(
    #     df_res_win_props[["AvgChange", "NumMatches"]]
    # )

    mod_win_props = smf.mixedlm(
        formula="Proportions ~ 1 + AvgChange + NumMatches",
        data=df_res_win_props,
        groups="Bookies",
        re_formula="1 + AvgChange",
    )

    res_mod_win_props = mod_win_props.fit(reml=True, method="lbfgs")

    fixed_effects = res_mod_win_props.fe_params
    random_effects = res_mod_win_props.random_effects

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
    ax.set(
        xlabel="$\\overline{\\Delta}(p_T, p_0)$", ylabel="$\\overline{\\pi}$"
    )
    finalize_plot(
        path=f"{cfg.paths.figures}win_props_re.pdf",
        save=cfg.general.save,
    )

    # legend = ax.legend(
    #     title="",
    #     bbox_to_anchor=(1.03, 0.5),
    #     loc="center left",
    #     labelspacing=0.05,
    #     borderaxespad=0,
    #     handletextpad=0.5,
    #     # handlelength=2,
    # )
    # plt.setp(legend.get_texts(), fontsize="small")

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

    # plt.legend(
    #     loc="upper left",
    #     ncol=3,
    #     fontsize=9,
    #     columnspacing=0.4,
    #     handlelength=1.5,
    # )

    tex_res_wp_re = res_mod_win_props.summary().as_latex().splitlines(True)
    tex_res_wp_re = tex_res_wp_re[19:-5]
    tex_res_wp_re.append("\\bottomrule\n")
    tex_res_wp_re[1] = "\\midrule\n"

    for bookie in bookies + ["All"]:
        res_win_props[bookie].rename(
            columns=dict(
                zip(
                    res_win_props[bookie].columns,
                    [
                        "$\Delta(p_T, p_0)$",
                        "$\overline{\Delta}(p_T, p_0)$",
                        "$\overline{C}$",
                        "$N$",
                        "$\overline{\pi}$",
                        "$Z$",
                        "$p$",
                    ],
                )
            ),
            inplace=True,
        )

        res_win_props[bookie][r"$\Delta(p_T, p_0)$"] = res_win_props[bookie][
            r"$\Delta(p_T, p_0)$"
        ].map(lambda x: "$" + str(x) + "$")
        res_win_props[bookie].loc[0:6, r"$\Delta(p_T, p_0)$"] = (
            res_win_props[bookie]
            .loc[0:6, r"$\Delta(p_T, p_0)$"]
            .str.replace("$[", "$]", regex=False)
        )
        res_win_props[bookie].loc[5::, r"$\Delta(p_T, p_0)$"] = (
            res_win_props[bookie]
            .loc[5::, r"$\Delta(p_T, p_0)$"]
            .str.replace("]$", "[$", regex=False)
        )

    # for bookies in PfdConf.BOOKIES:
    # endog = res_win_props[bookies]["Proportions"].copy()
    # exog = res_win_props[bookies]["AvgChange"].copy()
    # exog = sm.add_constant(exog)
    #
    # # Fit and summarize OLS model
    # mod = sm.OLS(endog=endog, exog=exog)
    # res = mod.fit(cov_type="HC1")
    # print(res.summary())
    # # res.resid.var()
    #
    # mod_wls = sm.WLS(endog, exog, weights=endog.var() /
    # res_win_props[bookies]["NumOddsMvt"])
    # res_wls = mod_wls.fit(cov_type="HC1")
    # print(res_wls.summary())
    # print(res_wls.summary().as_latex())

    # Odds Series

    # df = df.drop_duplicates(subset=["GroupId", "Update"])

    # df = df[df["NumOddsMvt"] > 1]
    # df = df.reset_index(drop=True)

    df["TsStart"] = df.groupby("Matchup")["Update"].transform("min")
    df["TsEnd"] = df.groupby("Matchup")["Update"].transform("max")

    df = df.set_index("Update")

    group_std = df.groupby("GroupId")["OddsMvt"].transform("std")
    df = df[group_std > 0]  # remove groups with zero odds variance

    def partition_list(lst, n_parts):
        # Calculate the size of each partition
        avg = len(lst) / float(n_parts)
        out = []
        last = 0.0

        while last < len(lst):
            out.append(lst[int(last) : int(last + avg)])
            last += avg

        return out

    def process_group(df_sub):
        return df_sub.groupby("GroupId").apply(
            resample,
            period=cfg.estimation.period,
            freq=cfg.estimation.resample_freq,
            pctls=np.arange(
                0, 1 + cfg.estimation.pctl / 100, cfg.estimation.pctl / 100
            ),
            include_groups=False,
        )

    def split_calc(df):
        partitions = partition_list(
            lst=list(df["Matchup"].unique()), n_parts=cfg.sampling.n_cores
        )

        with Pool(processes=os.cpu_count()) as pool:
            res_pool_resample = pool.map(
                process_group,
                [
                    df.loc[df["Matchup"].isin(partition)]
                    for partition in partitions
                ],
            )

        df = pd.concat(res_pool_resample, ignore_index=False)

        return df

    unique_group_ids = df["GroupId"].unique()
    num_unique_group_ids = df["GroupId"].nunique()

    split_points = [
        num_unique_group_ids // 4,
        num_unique_group_ids // 2,
        3 * num_unique_group_ids // 4,
    ]

    group_ids_part_1 = unique_group_ids[: split_points[0]]
    group_ids_part_2 = unique_group_ids[split_points[0] : split_points[1]]
    group_ids_part_3 = unique_group_ids[split_points[1] : split_points[2]]
    group_ids_part_4 = unique_group_ids[split_points[2] :]

    df_part_1 = split_calc(df=df.loc[df["GroupId"].isin(group_ids_part_1), :])
    df_part_2 = split_calc(df=df.loc[df["GroupId"].isin(group_ids_part_2), :])
    df_part_3 = split_calc(df=df.loc[df["GroupId"].isin(group_ids_part_3), :])
    df_part_4 = split_calc(df=df.loc[df["GroupId"].isin(group_ids_part_4), :])

    df = pd.concat(
        objs=[df_part_1, df_part_2, df_part_3, df_part_4], ignore_index=False
    )

    # df = df.groupby("GroupId").apply(
    #     resample,
    #     period=cfg.estimation.period,
    #     freq=cfg.estimation.resample_freq,
    #     pctls=np.arange(0, 1.02, 0.02),
    #     include_groups=False,
    # )

    df = df.reset_index(level=1, drop=True).reset_index(drop=False)

    # df.to_hdf(
    #     path_or_buf=f"{cfg.paths.data_intrm}data_resampled.h5",
    #     key="data_resampled",
    #     mode="w",
    # )

    group_std = df.groupby("GroupId")["OddsMvt"].transform("std")
    df = df[group_std > 0]  # remove groups with zero odds variance

    n_missings = df["OddsMvt"].isna().sum()
    frac_missings = n_missings / df["OddsMvt"].shape[0]

    df.to_hdf(
        path_or_buf=f"{cfg.paths.data_intrm}data_resampled.h5",
        key="data_resampled",
        mode="w",
    )

    # df = pd.read_hdf(
    #     path_or_buf=f"{cfg.paths.data_intrm}data_resampled.h5",
    #     key="data_resampled",
    #     mode="r",
    # )

    # bookies = sorted(list(df["Bookies"].unique()))
    # exog_cols = [col for col in df.columns if col.startswith("Compet")] + [
    #     "TsDur"
    # ]

    df["CumCount"] = df.groupby("GroupId").cumcount()

    n_per = int(df.shape[0] / df.groupby("GroupId").ngroups)
    # len_per = float(cfg.estimation.resample_freq.strip("min")) / 60
    odds_mvt_cols = [f"OddsMvt{i}" for i in range(0, n_per)]

    df = pivot_df(
        df=df,
        exog_cols=exog_cols + ["NumOddsMvt", "IsPro", "Match"],
        n_per=n_per,
    )

    df = impute_missings(df=df, seed=cfg.general.seed)

    # GARCH Model

    df_garch = df.melt(
        id_vars=["Matchup", "Bookies", "NumOddsMvt"] + exog_cols,
        value_name="OddsMvt",
        var_name="CumCount",
        value_vars=odds_mvt_cols,
    )

    df_garch = df_garch.loc[df_garch["NumOddsMvt"] < 20, :]
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

    cs_mean_rtrn = df_garch.groupby("CumCount")["Return"].mean().dropna()
    cs_mean_rtrn_sq = cs_mean_rtrn**2

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

    # tex_res_adf = (
    #     adf.regression.summary()
    #     .as_latex()
    #     .replace("\\textbf{", "")
    #     .replace("}", "")
    #     .splitlines(True)
    # )
    # indices = [i for i, x in enumerate(tex_res_adf) if x == "\\bottomrule\n"]
    # tex_res_adf_p1 = tex_res_adf[3 : indices[0] + 1]
    # tex_res_adf_p2 = tex_res_adf[indices[0] + 3 : indices[1] + 1]

    pacf_values, confint = pacf(
        x=cs_mean_rtrn**2,
        alpha=0.05,
        # nlags=len(cs_mean_rtrn),
        # qstat=True,
        # fft=True,
    )

    signific_idxs = np.where(
        ((confint[:, 0] <= 0) & (confint[:, 1] <= 0))
        | ((confint[:, 0] >= 0) & (confint[:, 1] >= 0))
    )

    garch_lags = signific_idxs[0].max()
    garch_lags = int(max(garch_lags, 1))

    pylab.rcParams.update(rcp_l)

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

    # Detrend time series
    # trend = np.arange(len(cs_mean_rtrn))
    # trend = sm.add_constant(trend)
    # mod_trend = sm.OLS(cs_mean_rtrn, trend).fit()
    # cs_mean_rtrn = cs_mean_rtrn - mod_trend.predict(trend)

    # Test GARCH Model
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
    res_garch = mod_garch.fit()

    params = res_garch.params
    omega = params["omega"]
    alpha = params["alpha[1]"]
    beta = params["beta[1]"]
    gamma = params["gamma[1]"]

    shock = np.linspace(-3, 3, 1000)
    cond_vola = np.exp(
        omega + alpha * (np.abs(shock) - np.sqrt(2 / np.pi)) + gamma * shock
    )

    # Plot the asymmetry shock response
    pylab.rcParams.update(rcp_s)

    _, ax = plt.subplots()
    ax.plot(shock, cond_vola, label="Conditional Volatility")
    # plt.title('Asymmetric Shock Response in EGARCH(1, 1) Model')
    ax.set(xlabel="Shock", ylabel="Conditional Volatility")
    finalize_plot(
        path=f"{cfg.paths.figures}asym_shock_resp.pdf",
        save=cfg.general.save,
    )
    # Plot the conditional volatility
    # fig, ax = plt.subplots()
    # ax.plot(res_garch.conditional_volatility)
    # ax.plot(cs_mean_rtrn_sq * 1e07)
    # ax.set(xlabel="Percentile Time Increments", ylabel="Volatility")
    # plt.xticks(
    #     np.arange(0, n_per, 1)[::5],
    #     np.arange(0, 100 + cfg.estimation.pctl, cfg.estimation.pctl)[::5],
    # )
    # finalize_plot(
    #     path=f"{cfg.paths.figures}egarch_cond_vola.pdf",
    #     save=cfg.general.save,
    # )

    tex_res_garch = (
        res_garch.summary()
        .as_latex()
        .replace("\\textbf{", "")
        .replace("}", "")
        .splitlines(True)
    )
    indices = [i for i, x in enumerate(tex_res_garch) if x == "\\bottomrule\n"]
    # tex_res_garch_p1 = tex_res_garch[3 : indices[0] + 1]
    tex_res_garch_p1 = tex_res_garch[indices[0] + 3 : indices[0] + 7]
    tex_res_garch_p2 = tex_res_garch[indices[0] + 9 : indices[1] + 1]
    tex_res_garch = tex_res_garch_p1 + tex_res_garch_p2

    # Unbiasedness Regressions

    df_ur = df.loc[df["NumOddsMvt"] < 20, :].copy()
    df_ur[odds_mvt_cols[1:]] = df_ur[odds_mvt_cols[1:]].subtract(
        df_ur["OddsMvt0"], axis=0
    )
    df_ur["Endog"] = df_ur["Match"] - df_ur["OddsMvt0"]
    # df_ur["Endog"] = df_ur[f"OddsMvt{n_per - 1}"] - df_ur["OddsMvt0"]

    res_ur: DefaultDict[Any, list] = defaultdict(list)

    part_fit_mixed_lm = partial(fit_mixed_lm, df_ur)

    with Pool() as pool:
        res_pool_ur = pool.map(part_fit_mixed_lm, odds_mvt_cols[1:])

    # for ele in bookies:
    #     print(res_pool_ur[1]["res"].random_effects[ele]["Exog"])

    for ele in res_pool_ur:
        res_ur["beta_1"].append(ele["beta_1"])
        res_ur["std_beta_1"].append(ele["std_beta_1"])
        res_ur["beta_0"].append(ele["beta_0"])
        res_ur["std_beta_0"].append(ele["std_beta_0"])
        res_ur["rmse"].append(ele["rmse"])

    signific_time_idx = (
        pd.Series(res_ur["beta_1"])
        + norm.ppf(0.975) * pd.Series(res_ur["std_beta_1"])
        > 1
    ) & (
        pd.Series(res_ur["beta_1"])
        - norm.ppf(0.975) * pd.Series(res_ur["std_beta_1"])
        < 1
    )
    signific_time_idx = (
        1 + signific_time_idx[signific_time_idx].index
    ) * cfg.estimation.pctl

    pylab.rcParams.update(rcp_m)

    plot_unbiased_reg_res(
        res_ur=res_ur,
        cfg=cfg,
        path=f"{cfg.paths.figures}unbiased_reg.pdf",
        save=cfg.general.save,
    )

    # Speed of Learning

    start_params = list(
        np.array(
            [
                np.random.uniform(low=0, high=1, size=10),
            ]
        ).T
    )
    start_params[0] = np.array([0.01])

    part_fit_gmm_mod = partial(
        fit_gmm_mod,
        df,
        n_per,
        cfg.estimation.incr,
        start_params,
        cfg.estimation.max_iter,
    )

    with Pool() as pool:
        res_gmm = pool.map(part_fit_gmm_mod, bookies)

    df_res_gmm = pd.DataFrame(data=[ele[0] for ele in res_gmm], index=bookies)

    gamma_stats_gmm = df_res_gmm["gamma"].agg(["mean", "min", "max"])
    idxmin_gamma_gmm = df_res_gmm["gamma"].idxmin()
    idxmax_gamma_gmm = df_res_gmm["gamma"].idxmax()

    # First-stage GMM
    part_fit_gmm_mod_first_stage = partial(
        fit_gmm_mod,
        df,
        n_per,
        cfg.estimation.incr,
        start_params[0],
        1,
    )

    with Pool() as pool:
        res_gmm_first_stage = pool.map(part_fit_gmm_mod_first_stage, bookies)

    pylab.rcParams.update(rcp_m)

    plot_gmm_res(
        res_gmm={"first_stage": res_gmm_first_stage, "cue": res_gmm},
        bookies=bookies,
        edgecolor=stata_colors[0],
        paths=[
            f"{cfg.paths.figures}gmm_params.pdf",
            f"{cfg.paths.figures}gmm_jstat.pdf",
            f"{cfg.paths.figures}gmm_pvalue.pdf",
        ],
        save=cfg.general.save,
    )

    # PyMC probabilistic modeling

    # trace = az.from_netcdf(
    #     filename=f"{cfg.paths.models}trace_{est_method}.nc"
    # )

    res_pm: DefaultDict[str, Any] = defaultdict(lambda: defaultdict())

    res_pm["vi"]["trace"], res_pm["vi"]["tracker"], res_pm["vi"]["advi"] = (
        gen_res_obj(
            df=df, est_method="advi", subset="tot", n_per=n_per, cfg=cfg
        )
    )

    res_pm["nuts_tot"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="tot", n_per=n_per, cfg=cfg
    )

    res_pm["nuts_pro"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="pro", n_per=n_per, cfg=cfg
    )

    res_pm["nuts_amat"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="amat", n_per=n_per, cfg=cfg
    )

    for key in list(res_pm.keys()):
        res_pm[key]["sum"] = az.summary(
            data=res_pm[key]["trace"],
            hdi_prob=cfg.sampling.hdi,
            stat_funcs=create_func_dict(),
            round_to=4,
        )
        res_pm[key]["sum"] = res_pm[key]["sum"][
            ~res_pm[key]["sum"].index.str.contains("interval__|log__")
        ].copy()

    pylab.rcParams.update(rcp_m)

    fig = plt.figure()
    mu_ax = fig.add_subplot(221)
    std_ax = fig.add_subplot(222)
    hist_ax = fig.add_subplot(212)
    mu_ax.plot(res_pm["vi"]["tracker"]["mean"])
    mu_ax.set(xlabel="", ylabel="Mean")
    std_ax.plot(res_pm["vi"]["tracker"]["std"])
    std_ax.set(xlabel="", ylabel="Std. Deviation")
    hist_ax.plot(res_pm["vi"]["advi"].hist)
    hist_ax.set(xlabel="Iterations", ylabel="Neg. ELBO")
    finalize_plot(
        path=f"{cfg.paths.figures}tracker_advi.pdf",
        save=cfg.general.save,
    )

    plot_traces(
        mod_trace=res_pm["nuts_tot"]["trace"],
        param="gamma",
        path=[
            f"{cfg.paths.figures}traces_gamma_tot_1.pdf",
            f"{cfg.paths.figures}traces_gamma_tot_2.pdf",
        ],
        save=cfg.general.save,
    )

    pylab.rcParams.update(rcp_l)

    plot_posteriors(
        mod_trace={
            "NUTS": res_pm["nuts_tot"]["trace"],
            "ADVI": res_pm["vi"]["trace"],
        },
        ref_vals=None,
        path=f"{cfg.paths.figures}post_gamma_tot.pdf",
        save=cfg.general.save,
    )

    plot_posteriors(
        mod_trace={
            "Professionals": res_pm["nuts_pro"]["trace"],
            "Amateurs": res_pm["nuts_amat"]["trace"],
        },
        ref_vals=round(res_pm["nuts_tot"]["sum"].at["mean_gamma", "mean"], 2),
        path=f"{cfg.paths.figures}post_gamma_nuts_pro_amat.pdf",
        save=cfg.general.save,
    )

    pylab.rcParams.update(rcp_s)

    plot_facetgrid(
        mod_trace=res_pm["vi"]["trace"],
        param="gamma",
        color_palette=stata_colors,
        path=f"{cfg.paths.figures}facetgrid_gamma_advi_tot.pdf",
        save=cfg.general.save,
    )

    plot_facetgrid(
        mod_trace=res_pm["nuts_tot"]["trace"],
        param="gamma",
        color_palette=stata_colors,
        path=f"{cfg.paths.figures}facetgrid_gamma_nuts_tot.pdf",
        save=cfg.general.save,
    )

    plot_facetgrid(
        mod_trace={
            "Professionals": res_pm["nuts_pro"]["trace"],
            "Amateurs": res_pm["nuts_amat"]["trace"],
        },
        param="gamma",
        color_palette=stata_colors,
        path=f"{cfg.paths.figures}facetgrid_gamma_nuts_pro_amat.pdf",
        save=cfg.general.save,
    )

    gamma_med_nuts = res_pm["nuts_tot"]["sum"].loc["mean_gamma", "median"]
    gamma_lower_nuts = res_pm["nuts_tot"]["sum"].loc["mean_gamma", "hdi_2.5%"]
    gamma_upper_nuts = res_pm["nuts_tot"]["sum"].loc["mean_gamma", "hdi_97.5%"]

    for key in list(res_pm.keys()):
        res_pm[key]["sum"] = format_sum(df=res_pm[key]["sum"], cfg=cfg)

    # test = pd.merge(
    #     left=sum_nuts_pro["mean"],
    #     right=sum_nuts_ama["mean"],
    #     how="left",
    #     on=sum_nuts_pro.index)

    # sns.violinplot(
    #     data=gamma_samples,
    #     x="Bookies",
    #     y="Samples",
    #     split=True,
    #     inner="quart"
    # )
    # plt.show()

    # fig, ax = plt.subplots()
    # az.plot_forest(
    #     trace_nuts,
    #     var_names=["gamma"],
    #     kind="forestplot",
    #     combined=True,
    #     ax=ax,
    #     # hdi_prob=hdi,
    #     # ridgeplot_overlap=10,
    #     # ridgeplot_alpha=0.5,
    # )
    # ax.set(xlabel=r"$\hat{\nu}_1$")
    # [tick.set_visible(False) for tick in ax.yaxis.get_ticklabels()]
    # for spine in ax.spines.values():
    #     spine.set_visible(True)
    #     spine.set_edgecolor("black")
    # plt.show()

    # sns.violinplot(data=df, x="class", y="age", split=True, inner="quart")

    # az.plot_trace(
    #     data=trace_advi,
    #     var_names=["sig_eps"],
    #     divergences=False,
    #     combined=False,
    #     compact=True,
    # )
    # plt.show(block=False)

    # Saving

    if cfg.general.save:
        df_desc.to_hdf(
            path_or_buf=f"{cfg.paths.data_proc}data_desc.h5",
            key="data_desc",
            mode="w",
        )

        values_to_save = {
            "iqr_rtrns": (iqr_rtrns, ".4f"),
            "n_obs": (n_obs, ","),
            "n_groups": (n_groups, None),
            "first_time_idx": (signific_time_idx[0], None),
            "last_time_idx": (signific_time_idx[-1], None),
            "gamma_med_nuts": (gamma_med_nuts, ".4f"),
            "gamma_lower_nuts": (gamma_lower_nuts, ".4f"),
            "gamma_upper_nuts": (gamma_upper_nuts, ".4f"),
            "is_amateur": (is_amateur, ".4f"),
            "is_pro": (is_pro, ".4f"),
            # "icc": (icc, ".4f"),
            "n_missings": (n_missings, None),
            "frac_missings": (frac_missings, ".4f"),
            "n_per": (n_per, ".0f"),
            # "len_per": (len_per, ".4g"),
            "avg_gamma_gmm": (gamma_stats_gmm["mean"], ".4f"),
            "min_gamma_gmm": (gamma_stats_gmm["min"], ".4f"),
            "max_gamma_gmm": (gamma_stats_gmm["max"], ".4f"),
            "idxmax_gamma_gmm": (idxmax_gamma_gmm, None),
            "idxmin_gamma_gmm": (idxmin_gamma_gmm, None),
            # "avg_phi_gmm": (avg_phi_gmm, ".4f"),
            "adf_stat": (adf_stat, ".2f"),
            "adf_p": (adf_p, ".4f"),
        }

        for key, (value, fmt) in values_to_save.items():
            save_values(
                key=key,
                value=value,
                file_name=f"{cfg.paths.vals}{cfg.files.vals}",
                fmt=fmt,
            )

        for key, value in cfg.sampling.items():
            save_values(
                key=key,
                value=value,
                file_name=f"{cfg.paths.vals}{cfg.files.vals}",
            )

        file_configs = [
            (f"{cfg.paths.tables}res_gpm.tex", "".join(tex_res_gpm)),
            (f"{cfg.paths.tables}res_rfa.tex", "".join(tex_res_rfa)),
            (f"{cfg.paths.tables}res_wp_re.tex", "".join(tex_res_wp_re)),
            (f"{cfg.paths.tables}res_garch.tex", "".join(tex_res_garch)),
        ]

        for file, body in file_configs:
            write_text_file(
                file=file, body=body, first_line=None, last_line=None
            )

        write_text_file(
            file=f"{cfg.paths.tables}res_rfa_tot.tex",
            body=mod_tex_tab(
                tab=df_res_rfa.apply(NumFormat.format_col)
                .style.format(na_rep="")
                .to_latex()
            ),
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_wp.tex",
            body=mod_tex_tab(
                tab=res_win_props["All"]
                .apply(NumFormat.format_col)
                .style.hide(axis="index")
                .format(na_rep="")
                .to_latex()
            ),
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_pm_mod.tex",
            body=mod_tex_tab(
                tab=res_pm["nuts_tot"]["sum"]
                .apply(NumFormat.format_col)
                .style.format(
                    formatter={
                        r"$\hat{R}$": NumFormat(my_format="{:.2f}").format_post
                    },
                    na_rep="NaN",
                )
                .to_latex()
            ),
        )

    # Execution Time and Log File Finish

    log.info(f"Execution time: {Logger.get_exec_time(start_time=t_start)}")


if __name__ == "__main__":
    run_estimation()
