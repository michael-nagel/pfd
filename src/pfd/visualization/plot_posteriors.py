#!/usr/bin/env python3

# Imports


import arviz as az
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from pfd.utils import finalize_plot

# Function


def plot_posteriors(
    mod_trace: az.InferenceData | dict[str, az.InferenceData] | list,
    ref_vals: float | list | None,
    path: str,
    save: bool,
) -> None:
    """
    Plot posterior distributions.

    Parameters
    ----------
    mod_trace : az.InferenceData | Dict[str, az.InferenceData] | list
        Record of the sampling process.
    ref_vals: float| list | None
        Reference values to be plotted.
    path : str
        Path for saving.
    save : bool
        Save figure if True.
    """
    if isinstance(mod_trace, dict):
        _, ax = plt.subplots(nrows=1, ncols=2, sharex="all", sharey="none")
        az.plot_posterior(
            mod_trace[list(mod_trace.keys())[0]],
            var_names=["mean_gamma"],
            hdi_prob=0.95,
            point_estimate="median",
            ref_val=ref_vals if ref_vals else {},
            # rope=[0, 0.5],
            ax=ax[0],
        )
        ax[0].set(
            title=list(mod_trace.keys())[0],
            xlabel="Average Learning Rate",
            # ylabel="Density",
        )
        az.plot_posterior(
            mod_trace[list(mod_trace.keys())[1]],
            var_names=["mean_gamma"],
            hdi_prob=0.95,
            point_estimate="median",
            ax=ax[1],
            ref_val=ref_vals if ref_vals else {},
        )
        ax[1].set(
            title=list(mod_trace.keys())[1],
            xlabel="Average Learning Rate",
            # ylabel="Density",
        )
        finalize_plot(path=path, save=save)

    elif isinstance(mod_trace, list):
        df_trace = pd.DataFrame(
            data=mod_trace,
            index=[f"{i * 10}-{(i + 1) * 10}" for i in range(0, 10)],
        ).T
        df_trace = df_trace.melt(
            var_name="Price Percentile Interval",
            value_name="Average Learning Rate",
        )

        _, ax = plt.subplots()
        sns.boxplot(
            data=df_trace,
            x="Price Percentile Interval",
            y="Average Learning Rate",
            # inner="quartile",
            ax=ax,
            showfliers=False,
            # linewidth=0.8,
            # density_norm="count",
            # width=0.5,
            # split=True,
            # cut=0,
        )
        if ref_vals:
            ax.axhline(y=ref_vals, color="black", linestyle="dotted")
        finalize_plot(path=path, save=save)

    else:
        _, ax = plt.subplots()
        az.plot_posterior(
            mod_trace,
            var_names=["mean_gamma"],
            hdi_prob=0.95,
            point_estimate="median",
            ref_val=ref_vals[0] if ref_vals else {},
            # rope=[0, 0.5],
            ax=ax,
        )
        ax.set(title="", xlabel="Average Learning Rate", ylabel="")
        finalize_plot(path=path, save=save)
