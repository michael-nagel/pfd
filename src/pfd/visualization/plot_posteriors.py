#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from typing import Dict

import arviz as az
import matplotlib.pyplot as plt

from pfd.utils import finalize_plot

# Function


def plot_posteriors(
    mod_trace: az.InferenceData | Dict[str, az.InferenceData],
    ref_vals: float | list | None,
    path: str,
    save: bool,
) -> None:
    """
    Plot posterior distributions.

    Parameters
    ----------
    mod_trace : az.InferenceData | Dict[str, az.InferenceData]
        Record of the sampling process.
    ref_vas: float| list | None
        Reference values to be plotted.
    path : str
        Path for saving.
    save : bool
        Save figure if True.
    """
    if isinstance(mod_trace, dict):
        _, ax = plt.subplots(nrows=1, ncols=2, sharex="all", sharey="none")
        az.plot_posterior(
            mod_trace["Professionals"],
            var_names=["mean_gamma"],
            hdi_prob=0.95,
            point_estimate="median",
            ref_val=ref_vals if ref_vals else {},
            # rope=[0, 0.5],
            ax=ax[0],
        )
        ax[0].set(
            title=list(mod_trace.keys())[0],
            xlabel="$\\widebar{\\,\\gamma}$",
            ylabel="Density",
        )
        az.plot_posterior(
            mod_trace["Amateurs"],
            var_names=["mean_gamma"],
            hdi_prob=0.95,
            point_estimate="median",
            ax=ax[1],
            ref_val=ref_vals if ref_vals else {},
        )
        ax[1].set(
            title=list(mod_trace.keys())[1],
            xlabel="$\\widebar{\\,\\gamma}$",
            ylabel="Density",
        )
        finalize_plot(path=path, save=save)

    else:
        _, ax = plt.subplots(nrows=1, ncols=2)
        az.plot_posterior(
            mod_trace,
            var_names=["mean_gamma"],
            hdi_prob=0.95,
            point_estimate="median",
            ref_val=ref_vals[0] if ref_vals else {},
            # rope=[0, 0.5],
            ax=ax[0],
        )
        ax[0].set(title="", xlabel="$\\widebar{\\gamma}$", ylabel="Density")
        az.plot_posterior(
            mod_trace,
            var_names=["mean_Phi"],
            hdi_prob=0.95,
            point_estimate="median",
            # # rope=[-0.001, 0.001],
            ax=ax[1],
            ref_val=ref_vals[1] if ref_vals else {},
        )
        ax[1].set(title="", xlabel="$\\widebar{\\,\\Phi}$", ylabel="")
        ax[1].ticklabel_format(style="sci", scilimits=(0, 0), axis="x")
        finalize_plot(path=path, save=save)
