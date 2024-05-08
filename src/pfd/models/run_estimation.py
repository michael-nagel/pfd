#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file runs the estimation procedure.
"""

# Imports

import json
from collections import defaultdict
from functools import partial
from multiprocessing import Pool
from typing import Any, DefaultDict, Tuple

import arviz as az
import hydra
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from hydra import compose, initialize
from hydra.core.config_store import ConfigStore

from pfd.helpers import (
    create_pm_mod,
    fit_gmm_mod,
    fit_rfa_mod,
    impute_missings,
    save_tex_vals,
)
from pfd.utils import (
    Logger,
    NumFormat,
    PFDConfig,
    PlotParams,
    calc_win_props,
    create_func_dict,
    enc_categ_var,
    est_pm_mod,
    finalize_plot,
    fit_mixed_lm,
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

    df_desc = df.copy()

    df = df[
        [
            "Matchup",
            "GroupId",
            "Competition",
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

    bookies = sorted(list(df["Bookies"].unique()))

    df["IsPro"] = 0
    df.loc[df["Competition"].isin(["ATP", "WTA"]), "IsPro"] = 1

    is_amateur, is_pro = df["IsPro"].value_counts(True).tolist()

    df = enc_categ_var(
        df=df,
        col="Competition",
        prefix="Compet",
        rm_first=True,
        rm_categ_var=True,
    )

    df["TsDur"] = scale_vars(df["TsDur"].to_numpy().reshape(-1, 1))

    # Relative Forecast Accuracy of Opening and Closing Lines

    df_oc = df.groupby("GroupId", as_index=False).first()

    df_oc["DltOpnCls"] = df_oc["ClsOdds"] - df_oc["OpnOdds"]
    df_oc = df_oc[df_oc["DltOpnCls"].abs() > 0]

    df_oc["FEOpn"] = (df_oc["Match"] - df_oc["OpnOdds"]).abs()
    df_oc["FECls"] = (df_oc["Match"] - df_oc["ClsOdds"]).abs()

    pylab.rcParams.update(rcp_s)

    _, ax = plt.subplots()
    sns.histplot(data=df_oc, x="DltOpnCls", stat="density")
    ax.set(xlabel="Delta")
    finalize_plot(
        path=f"{cfg.paths.figures}delta_opn_cls.pdf", save=cfg.general.save
    )

    exog_cols = [col for col in df_oc.columns if col.startswith("Compet")] + [
        "TsDur"
    ]

    part_fit_rfa_mod = partial(fit_rfa_mod, df_oc, exog_cols)

    with Pool() as pool:
        res_rfa = pool.map(part_fit_rfa_mod, bookies + ["All"])

    res_rfa_re = res_rfa[-1]["fitted_model"]

    group_var = res_rfa_re.cov_re.iat[0, 0]
    resid_var = res_rfa_re.scale
    icc = group_var / (group_var + resid_var)  # Calculate ICC

    tex_res_rfa = res_rfa_re.summary().as_latex().splitlines(True)
    tex_res_rfa_p1 = tex_res_rfa[5:13]  # export part 1 to latex
    tex_res_rfa_p2 = tex_res_rfa[18:-4]  # export part 2 to latex

    df_res_rfa = pd.DataFrame(data=res_rfa, index=bookies + ["All"])
    df_res_rfa = df_res_rfa.loc[:, df_res_rfa.columns != "fitted_model"]

    df_res_rfa = df_res_rfa.rename(
        columns=dict(
            zip(
                df_res_rfa.columns,
                [
                    "$N$",
                    "$rmse(e_1)$",
                    "$rmse(e_2)$",
                    r"$\beta_0$",
                    r"$\beta_1$",
                    r"$p_{\beta_0}$",
                    r"$p_{\beta_1}$",
                ],
            )
        )
    )

    # Magnitude and Direction of Odds Movements
    res_win_props: DefaultDict[Any, list] = defaultdict(list)

    ivals = [
        [-np.inf, -0.15],
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
        [0.15, np.inf],
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
    # TODO plot random effects using line plot?

    df_res_win_props = pd.concat(res_win_props, ignore_index=True)

    df_res_win_props["Bookies"] = np.repeat(
        a=list(res_win_props.keys()),
        repeats=res_win_props[bookies[0]].shape[0],
    )

    df_res_win_props[["AvgChange", "NumMatches"]] = scale_vars(
        df_res_win_props[["AvgChange", "NumMatches"]]
    )

    mod_win_props = smf.mixedlm(
        formula="Proportions ~ 1 + AvgChange + NumMatches",
        data=df_res_win_props,
        groups="Bookies",
        re_formula="1 + AvgChange",
    )

    res_mod_win_props = mod_win_props.fit(reml=True, method="lbfgs")
    # ["bfgs", "lbfgs", "cg"]

    tex_res_wp = res_mod_win_props.summary().as_latex().splitlines(True)
    tex_res_wp_p1 = tex_res_wp[5:13]  # export part 1 to latex
    tex_res_wp_p2 = tex_res_wp[18:-4]  # export part 2 to latex

    for bookie in bookies + ["All"]:
        res_win_props[bookie].rename(
            columns=dict(
                zip(
                    res_win_props[bookie].columns,
                    [
                        r"$\Delta(Q_T, Q_1)$",
                        r"$\overline{\Delta}(Q_T, Q_1)$",
                        r"$\overline{C}$",
                        "$N$",
                        r"$\pi$",
                        "$Z$",
                        "$p$",
                    ],
                )
            ),
            inplace=True,
        )

        res_win_props[bookie][r"$\Delta(Q_T, Q_1)$"] = res_win_props[bookie][
            r"$\Delta(Q_T, Q_1)$"
        ].map(lambda x: "$" + str(x) + "$")
        res_win_props[bookie].loc[0:6, r"$\Delta(Q_T, Q_1)$"] = (
            res_win_props[bookie]
            .loc[0:6, r"$\Delta(Q_T, Q_1)$"]
            .str.replace("$[", "$]", regex=False)
        )
        res_win_props[bookie].loc[5::, r"$\Delta(Q_T, Q_1)$"] = (
            res_win_props[bookie]
            .loc[5::, r"$\Delta(Q_T, Q_1)$"]
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

    # Unbiasedness Regressions

    # df = df.drop_duplicates(subset=["GroupId", "Update"])

    df = df[df["NumOddsMvt"] > 4]
    df = df.reset_index(drop=True)

    df["TsStart"] = df.groupby("Matchup")["Update"].transform("min")
    df["TsEnd"] = df.groupby("Matchup")["Update"].transform("max")

    df = df.set_index("Update")

    # df_x = df[df["NumOddsMvt"] > 4]
    # df_sub_1 = df_x.groupby("GroupId").last()
    # df_sub_2 = df_x.loc[
    #     df_x["TsEnd"] - pd.Timedelta(hours=2) < df_x.index
    # ].copy()
    # df_sub_2 = df_sub_2.groupby("GroupId").first()
    # df_sub = pd.merge(
    #     left=df_sub_1, right=df_sub_2, how="inner", on="GroupId"
    #     )
    # print((df_sub.OddsMvt_x == df_sub.OddsMvt_y).sum() / len(df_sub))

    df = df.groupby("GroupId").apply(
        resample,
        period=cfg.estimation.period,
        freq=cfg.estimation.resample_freq,
        include_groups=False,
    )

    df = df.reset_index(level=1, drop=True).reset_index()

    n_missings = df["OddsMvt"].isna().sum()

    # def calc_elap_time(group):
    #     group["ElapTime"] = group["Update"].diff().fillna(
    #         pd.Timedelta(seconds=0)
    #     ).cumsum() / pd.Timedelta(hours=1)
    #     return group

    # # Apply the function to each group
    # df = df.groupby("GroupId").apply(calc_elap_time)

    # df["ElapTime"] = df.groupby("GroupId")["Update"].diff().fillna(
    #     pd.Timedelta(seconds=0)
    # ).cumsum() / pd.Timedelta(hours=1)

    # Keep every 5% percentile of variable "PctElapTime"
    # df = df.groupby("GroupId", group_keys=False).apply(
    # keep_pctls, np.arange(0, 1.05, 0.05)
    # )

    df.to_hdf(
        path_or_buf=f"{cfg.paths.data_intrm}data_resampled.h5",
        key="data_resampled",
        mode="w",
    )

    # df = pd.read_hdf(
    #     path_or_buf=f"{cfg.paths.data_intrm}data_resampled.h5",
    #     key="data_resampled",
    # )
    # bookies = sorted(list(df["Bookies"].unique()))
    # exog_cols = [col for col in df.columns if col.startswith("Compet")] + [
    #     "TsDur"
    # ]

    group_std = df.groupby("GroupId")["OddsMvt"].transform("std")
    df = df[group_std > 0]  # remove groups with zero odds variance

    df["CumCount"] = df.groupby("GroupId").cumcount()

    n_per = int(df.shape[0] / df.groupby("GroupId").ngroups)
    len_per = float(cfg.estimation.resample_freq.strip("min")) / 60
    odds_mvt_cols = [f"OddsMvt{i}" for i in range(1, n_per - 1)]

    df = pivot_df(
        df=df, exog_cols=exog_cols + ["NumOddsMvt", "IsPro"], n_per=n_per
    )

    df = impute_missings(df=df, seed=cfg.general.seed)

    df_ur = df.loc[df["NumOddsMvt"] < 20, :].copy()
    df_ur[odds_mvt_cols] = df_ur[odds_mvt_cols].subtract(
        df_ur["OddsMvt0"], axis=0
    )
    df_ur["Endog"] = df_ur[f"OddsMvt{n_per - 1}"] - df_ur["OddsMvt0"]

    res_ur: DefaultDict[Any, list] = defaultdict(list)

    part_fit_mixed_lm = partial(fit_mixed_lm, df_ur)

    with Pool() as pool:
        res_pool_ur = pool.map(part_fit_mixed_lm, odds_mvt_cols)

    for ele in res_pool_ur:
        res_ur["beta_1"].append(ele["beta_1"])
        res_ur["std_beta_1"].append(ele["std_beta_1"])
        res_ur["beta_0"].append(ele["beta_0"])
        res_ur["std_beta_0"].append(ele["std_beta_0"])
        res_ur["rmse"].append(ele["rmse"])

    pylab.rcParams.update(rcp_m)

    plot_unbiased_reg_res(
        res_ur=res_ur,
        len_per=len_per,
        path=f"{cfg.paths.figures}unbiased_reg.pdf",
        save=cfg.general.save,
    )

    # Speed of Learning

    start_params = list(
        np.array(
            [
                np.random.uniform(low=0, high=5, size=10),
                np.random.uniform(low=-0.25, high=0.25, size=10),
            ]
        ).T
    )
    start_params[0] = np.array([1, 0.01])

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

    avg_gamma_gmm = df_res_gmm["gamma"].mean()
    avg_phi_gmm = df_res_gmm["Phi"].mean()

    # df_res_gmm = df_res_gmm.rename(
    #     columns=dict(
    #         zip(
    #             df_res_gmm.columns,
    #             [
    #                 "$\hat{\gamma}$",
    #                 "$s.e.(\hat{\gamma})$",
    #                 "$\hat{\Phi}$",
    #                 "$s.e.(\hat{\Phi})$",
    #                 "$\J$",
    #                 "$p$",
    #             ],
    #         )
    #     )
    # )

    # print(gmm_mod.momcond(start_params).shape)
    # optim_method="nm", inv_weights=np.eye(N=14))
    # gmm_res.model.exog_names[:] = "Gamma K".split()
    # print(gmm_res_cue.summary(xname=[r"$\hat{\gamma}$", r"$\hat{K}$"]))
    # print(gmm_mod.momcond_mean(gmm_res_cue.params))
    # print(df_res_gmm["gamma"].mean())

    pylab.rcParams.update(rcp_m)

    plot_gmm_res(
        res_gmm=res_gmm,
        bookies=bookies,
        edgecolor=stata_colors[0],
        paths=[
            f"{cfg.paths.figures}gmm_params.pdf",
            f"{cfg.paths.figures}gmm_jstat.pdf",
            f"{cfg.paths.figures}gmm_params_start_vals.pdf",
        ],
        save=cfg.general.save,
    )

    # PyMC probabilistic modeling
    # TODO helper fct?
    def gen_res_obj(
        df: pd.DataFrame, est_method: str, subset: str
    ) -> Tuple[Any, Any, Any] | az.InferenceData:
        """
        Generate the result objects for ADVI and NUTS.

        Parameters
        ----------
        df: pd.DataFrame
            Input DataFrame.
        est_method : str
            Estimation method ("advi" or "nuts").
        subset: str
            Which subset of the data should be used for estimation.
            Possible arguments are [tot, pro, amat].

        Returns
        -------
        Tuple[Any, Any, Any] | az.InferenceData
            Results for either ADVI or NUTS.
        """
        if subset not in ["tot", "pro", "amat"]:
            raise ValueError("subset must be 'tot', 'pro' or 'amat'")

        if subset == "pro":
            df = df.loc[df["IsPro"] == 1]
        elif subset == "amat":
            df = df.loc[df["IsPro"] == 0]
        else:
            pass

        model = create_pm_mod(df=df, n_per=n_per, incr=cfg.estimation.incr)

        if est_method == "advi":
            trace, tracker, advi = est_pm_mod(
                model=model,
                seed=cfg.general.seed,
                vi=True,
                vi_n_iter=100,
                vi_n_draws=100,
            )

            return trace, tracker, advi

        elif est_method == "nuts":
            trace = est_pm_mod(
                model=model,
                seed=cfg.general.seed,
                n_draws=500,
                n_tune=100,
                n_chains=cfg.sampling.n_chains,
                n_cores=cfg.sampling.n_cores,
                targ_acpt=cfg.sampling.targ_acpt,
            )

        else:
            raise ValueError("est_method must be either 'advi' or 'nuts'")

        trace.to_netcdf(
            filename=f"{cfg.paths.models}trace_{est_method}_{subset}.nc"
        )

        return trace

    # trace = az.from_netcdf(
    #     filename=f"{cfg.paths.models}trace_{est_method}.nc"
    # )

    res_pm: DefaultDict[str, Any] = defaultdict(lambda: defaultdict())

    res_pm["vi"]["trace"], res_pm["vi"]["tracker"], res_pm["vi"]["advi"] = (
        gen_res_obj(df=df, est_method="advi", subset="tot")
    )
    res_pm["nuts_tot"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="tot"
    )
    res_pm["nuts_pro"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="pro"
    )
    res_pm["nuts_amat"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="amat"
    )

    summary_advi = az.summary(
        data=res_pm["vi"]["trace"],
        hdi_prob=cfg.sampling.hdi,
        stat_funcs=create_func_dict(),
        round_to=4,
    )

    summary_nuts_tot = az.summary(
        data=res_pm["nuts_tot"]["trace"],
        hdi_prob=cfg.sampling.hdi,
        stat_funcs=create_func_dict(),
        round_to=4,
    )

    pylab.rcParams.update(rcp_m)

    fig = plt.figure()
    mu_ax = fig.add_subplot(221)
    std_ax = fig.add_subplot(222)
    hist_ax = fig.add_subplot(212)
    mu_ax.plot(res_pm["vi"]["tracker"]["mean"])
    mu_ax.set(title="Mean Track", xlabel="Iterations", ylabel="Value")
    std_ax.plot(res_pm["vi"]["tracker"]["std"])
    std_ax.set(title="Std.Track", xlabel="Iterations", ylabel="Value")
    hist_ax.plot(res_pm["vi"]["advi"].hist)
    hist_ax.set(title="Neg. ELBO Track", xlabel="Iterations", ylabel="Value")
    finalize_plot(
        path=f"{cfg.paths.figures}tracker_advi.pdf",
        save=cfg.general.save,
    )

    pylab.rcParams.update(rcp_l)

    plot_posteriors(
        mod_trace=res_pm["vi"]["trace"],
        ref_vals=None,
        path=f"{cfg.paths.figures}post_means_advi.pdf",
        save=cfg.general.save,
    )

    plot_posteriors(
        mod_trace=res_pm["nuts_tot"]["trace"],
        ref_vals=None,
        path=f"{cfg.paths.figures}post_means_nuts_tot.pdf",
        save=cfg.general.save,
    )

    plot_posteriors(
        mod_trace={
            "Professionals": res_pm["nuts_pro"]["trace"],
            "Amateurs": res_pm["nuts_amat"]["trace"],
        },
        ref_vals=round(summary_advi.at["mean_gamma", "mean"], 2),
        path=f"{cfg.paths.figures}post_means_nuts_pro_amat.pdf",
        save=cfg.general.save,
    )

    pylab.rcParams.update(rcp_m)

    plot_traces(
        mod_trace=res_pm["nuts_tot"]["trace"],
        param="gamma",
        path=f"{cfg.paths.figures}traces_gamma_nuts_tot.pdf",
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
            "Amateurs": res_pm["nuts_pro"]["trace"],
        },
        param="gamma",
        color_palette=stata_colors,
        path=f"{cfg.paths.figures}facetgrid_gamma_nuts_pro_amat.pdf",
        save=cfg.general.save,
    )

    hdi_lwr = round(((1 - cfg.sampling.hdi) / 2) * 100, 2)
    hdi_upr = round((1 - (1 - cfg.sampling.hdi) / 2) * 100, 2)
    cols_nuts = [
        "mean",
        "sd",
        "median",
        "std_median",
        f"hdi_{hdi_lwr}%",
        f"hdi_{hdi_upr}%",
        "r_hat",
    ]

    def format_sum_nuts(sum_nuts: pd.DataFrame) -> pd.DataFrame:
        """
        Format sum_nuts DataFrame.

        Parameters
        ----------
        sum_nuts : pd.DataFrame
            Summary DataFrame obtained from NUTS sampling.

        Returns
        -------
        pd.DataFrame
            Formatted DataFrame.
        """
        sum_nuts = sum_nuts[cols_nuts]
        sum_nuts = sum_nuts.rename(
            columns={
                "sd": "std_mean",
                f"hdi_{hdi_lwr}%": f"$hdi^{{{hdi_lwr}}}\\%$",
                f"hdi_{hdi_upr}%": f"$hdi^{{{hdi_upr}}}\\%$",
                "r_hat": "$\\hat{R}$",
            }
        )

        rows_nuts = (
            ["mean_gamma", "sd_gamma"]
            + [row for row in sum_nuts.index if row.startswith("gamma[")]
            + ["mean_Phi", "sd_Phi"]
            + [row for row in sum_nuts.index if row.startswith("Phi[")]
            + ["sd_eps"]
        )
        sum_nuts = sum_nuts.loc[rows_nuts, :]

        sum_nuts = sum_nuts.rename(
            index={
                "mean_gamma": "$\\hat{\\mu}_{\\gamma}$",
                "mean_Phi": "$\\hat{\\mu}_{\\Phi}$",
                "sd_gamma": "$\\hat{\\sigma}_{\\gamma}$",
                "sd_Phi": "$\\hat{\\sigma}_{\\Phi}$",
                "sd_eps": "$\\hat{\\sigma}$",
            }
        )

        new_index = {
            idx: idx.replace("gamma[", "$\\hat{\\gamma}_{")
            .replace("Phi[", "$\\hat{\\Phi}_{")
            .replace("]", "}$")
            for idx in sum_nuts.index
        }
        sum_nuts = sum_nuts.rename(index=new_index)
        return sum_nuts

    sum_nuts = format_sum_nuts(sum_nuts=sum_nuts)
    sum_nuts_pro = format_sum_nuts(sum_nuts=sum_nuts_pro)
    sum_nuts_amat = format_sum_nuts(sum_nuts=sum_nuts_amat)

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

        values_path = f"{cfg.paths.vals}{cfg.files.vals}"
        save_tex_vals(key="n_obs", value=n_obs, file_name=values_path)
        save_tex_vals(
            key="is_amateur",
            value=is_amateur,
            file_name=values_path,
            fmt=".2%",
        )
        save_tex_vals(
            key="is_pro", value=is_pro, file_name=values_path, fmt=".2%"
        )
        save_tex_vals(key="icc", value=icc, file_name=values_path)
        save_tex_vals(
            key="n_missings", value=n_missings, file_name=values_path
        )
        save_tex_vals(key="n_per", value=n_per, file_name=values_path)
        save_tex_vals(key="len_per", value=len_per, file_name=values_path)
        save_tex_vals(
            key="avg_gamma_gmm", value=avg_gamma_gmm, file_name=values_path
        )
        save_tex_vals(
            key="avg_phi_gmm", value=avg_phi_gmm, file_name=values_path
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_rfa_p1.tex",
            body="".join(tex_res_rfa_p1),
            first_line=None,
            last_line=None,
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_rfa_p2.tex",
            body="".join(tex_res_rfa_p2),
            first_line=None,
            last_line=None,
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_rfa_tot.tex",
            body=df_res_rfa.apply(NumFormat.format_col)
            .style.format(na_rep="")
            .to_latex(),
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_wp_p1.tex",
            body="".join(tex_res_wp_p1),
            first_line=None,
            last_line=None,
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_wp_p2.tex",
            body="".join(tex_res_wp_p2),
            first_line=None,
            last_line=None,
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_wp_re.tex",
            body=res_win_props["All"]
            .apply(NumFormat.format_col)
            .style.hide(axis="index")
            .format(na_rep="")
            .to_latex(),
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_pm_mod.tex",
            body=sum_nuts.apply(NumFormat.format_col)
            .style.format(
                formatter={
                    r"$\hat{R}$": NumFormat(my_format="{:.2f}").format_post
                },
                na_rep="",
            )
            .to_latex(),
        )

    # Execution Time and Log File Finish

    log.info(f"Execution time: {Logger.get_exec_time(start_time=t_start)}")


if __name__ == "__main__":
    run_estimation()
