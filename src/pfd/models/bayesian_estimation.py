#!/usr/bin/env python3

"""
This file estimates the learning rate using Bayesian methods.
"""

# Imports

from collections import defaultdict
from typing import Any

import arviz as az
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from pfd.helpers import gen_res_obj
from pfd.utils import (
    PFDConfig,
    PlotParams,
    create_func_dict,
    finalize_plot,
    format_sum,
)
from pfd.visualization import plot_facetgrid, plot_posteriors, plot_traces

# Function


def estimate_bayesian_learning_rate(
    df: pd.DataFrame,
    n_per: int,
    rmse: pd.Series,
    cfg: PFDConfig,
    plot_params: PlotParams,
    stata_colors: list,
) -> tuple[dict, pd.DataFrame, float, float, float, float, float, float, float]:
    """
    Estimate the learning rate using Bayesian methods.

    This function estimates the bookmaker-specific learning rate using
    ADVI and NUTS, for the total sample as well as favorites/longshots,
    professionals/amateurs, and a 10x partition by opening odds.

    Parameters
    ----------
    df : pd.DataFrame
        Wide-format, imputed estimation sample.
    n_per : int
        Number of periods of the time series.
    rmse : pd.Series
        RMSE of the opening odds for each bookmaker.
    cfg : PFDConfig
        Config parameters.
    plot_params : PlotParams
        Plotting parameters.
    stata_colors : list
        Color palette.

    Returns
    -------
    tuple
        res_pm, metrics, gamma_med_nuts, gamma_lower_nuts,
        gamma_upper_nuts, gamma_fav, gamma_udd, gamma_pro, gamma_amat.
    """
    # Partition observations according to 10 equally spaced intervals according
    # to the size of the opening odds
    split_points = np.quantile(np.sort(df["OddsMvt0"]), np.linspace(0, 1, 11))

    masks = [
        (df["OddsMvt0"] > split_points[i])
        & (df["OddsMvt0"] <= split_points[i + 1])
        for i in range(len(split_points) - 1)
    ]

    for i in range(0, 10):
        df.loc[masks[i], "Quantile"] = i + 1

    # Container for estimation output
    res_pm: defaultdict[str, Any] = defaultdict(lambda: defaultdict())

    # Estimation using ADVI & total sample
    res_pm["vi"]["trace"], res_pm["vi"]["tracker"], res_pm["vi"]["advi"] = (
        gen_res_obj(
            df=df, est_method="advi", subset="tot", n_per=n_per, cfg=cfg
        )
    )

    # Estimation using NUTS & total sample
    res_pm["nuts_tot"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="tot", n_per=n_per, cfg=cfg
    )

    # Estimation using NUTS & favorites
    res_pm["nuts_fav"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="fav", n_per=n_per, cfg=cfg
    )

    # Estimation using NUTS & underdogs
    res_pm["nuts_udd"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="udd", n_per=n_per, cfg=cfg
    )

    # Estimation using NUTS & 10x partitioned sample
    for i in range(0, 10):
        res_pm[f"nuts_q{i + 1}"]["trace"] = gen_res_obj(
            df=df,
            est_method="nuts",
            subset=f"quantile{i + 1}",
            n_per=n_per,
            cfg=cfg,
        )

    # Estimation using NUTS & professionals
    res_pm["nuts_pro"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="pro", n_per=n_per, cfg=cfg
    )

    # Estimation using NUTS & amateurs
    res_pm["nuts_amat"]["trace"] = gen_res_obj(
        df=df, est_method="nuts", subset="amat", n_per=n_per, cfg=cfg
    )

    # Create summary statistics
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

    # Correlate log loss with bookmaker-specific median learning rate and plot

    gamma = res_pm["nuts_tot"]["sum"]["median"].iloc[3:]
    gamma.index = gamma.index.str.replace("gamma[", "").str.replace("]", "")
    metrics = pd.merge(
        left=pd.DataFrame({"RMSE": rmse}),
        right=pd.DataFrame({"Learning Rate": gamma}),
        how="inner",
        left_index=True,
        right_index=True,
    )

    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_small", fig_size=(6.4, 4.8))
    )

    _, ax = plt.subplots()
    plt.tight_layout()
    sns.regplot(data=metrics, x="RMSE", y="Learning Rate", ax=ax)
    # Make every second tick invisible
    [
        tick.set_visible(False)
        for i, tick in enumerate(ax.xaxis.get_major_ticks())
        if i % 2 != 0
    ]
    finalize_plot(
        path=f"{cfg.paths.figures}scatter_gamma_loss.pdf",
        save=cfg.general.save,
    )

    # Plot the tracker of ADVI
    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_big", fig_size=(6.4, 4.8))
    )

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

    # Plot the traces (NUTS for total sample)
    plot_traces(
        mod_trace=res_pm["nuts_tot"]["trace"],
        param="gamma",
        path=[
            f"{cfg.paths.figures}traces_gamma_tot_1.pdf",
            f"{cfg.paths.figures}traces_gamma_tot_2.pdf",
        ],
        save=cfg.general.save,
    )

    # Plot the posteriors (NUTS and ADVI for total sample)
    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_big", fig_size=(6.4, 2.8))
    )

    plot_posteriors(
        mod_trace={
            "NUTS": res_pm["nuts_tot"]["trace"],
            "ADVI": res_pm["vi"]["trace"],
        },
        ref_vals=None,
        path=f"{cfg.paths.figures}post_gamma_tot.pdf",
        save=cfg.general.save,
    )

    # Plot the posteriors for favorites and longshots (NUTS)
    plot_posteriors(
        mod_trace={
            "Favorites": res_pm["nuts_fav"]["trace"],
            "Longshots": res_pm["nuts_udd"]["trace"],
        },
        ref_vals=round(res_pm["nuts_tot"]["sum"].at["mean_gamma", "median"], 2),
        path=f"{cfg.paths.figures}post_gamma_nuts_fav_udd.pdf",
        save=cfg.general.save,
    )

    # Plot the posteriors for the 10x partitioned sample (NUTS)
    plot_posteriors(
        mod_trace=[
            res_pm[f"nuts_q{i + 1}"]["trace"]
            .posterior["mean_gamma"]
            .to_numpy()
            .flatten()
            for i in range(0, 10)
        ],
        ref_vals=round(res_pm["nuts_tot"]["sum"].at["mean_gamma", "median"], 2),
        path=f"{cfg.paths.figures}post_gamma_nuts_ivals.pdf",
        save=cfg.general.save,
    )

    # Plot the posteriors for professionals and amateurs (NUTS)
    plot_posteriors(
        mod_trace={
            "Professionals": res_pm["nuts_pro"]["trace"],
            "Amateurs": res_pm["nuts_amat"]["trace"],
        },
        ref_vals=round(res_pm["nuts_tot"]["sum"].at["mean_gamma", "median"], 2),
        path=f"{cfg.paths.figures}post_gamma_nuts_pro_amat.pdf",
        save=cfg.general.save,
    )

    # Plot the bookmaker specific posteriors (ADVI and NUTS)
    pylab.rcParams.update(
        plot_params.set_rc_params(kind="fig_small", fig_size=(6.4, 4.8))
    )

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

    # Store some values
    gamma_med_nuts = res_pm["nuts_tot"]["sum"].loc["mean_gamma", "median"]
    gamma_lower_nuts = res_pm["nuts_tot"]["sum"].loc["mean_gamma", "hdi_2.5%"]
    gamma_upper_nuts = res_pm["nuts_tot"]["sum"].loc["mean_gamma", "hdi_97.5%"]
    gamma_fav = res_pm["nuts_fav"]["sum"].loc["mean_gamma", "median"]
    gamma_udd = res_pm["nuts_udd"]["sum"].loc["mean_gamma", "median"]
    gamma_pro = res_pm["nuts_pro"]["sum"].loc["mean_gamma", "median"]
    gamma_amat = res_pm["nuts_amat"]["sum"].loc["mean_gamma", "median"]

    # Format summary statistics
    for key in list(res_pm.keys()):
        res_pm[key]["sum"] = format_sum(df=res_pm[key]["sum"], cfg=cfg)

    # The ADVI tracker and the ADVI object itself are consumed above, in the
    # convergence figure, and nothing downstream reads them; their arrays are
    # already on disk as tracker_mean.npy, tracker_std.npy and advi_hist.npy.
    # They hold bound pytensor methods and would otherwise travel out of this
    # function as unpicklable baggage.
    for key in ("tracker", "advi"):
        res_pm["vi"].pop(key, None)

    return (
        res_pm,
        metrics,
        gamma_med_nuts,
        gamma_lower_nuts,
        gamma_upper_nuts,
        gamma_fav,
        gamma_udd,
        gamma_pro,
        gamma_amat,
    )
