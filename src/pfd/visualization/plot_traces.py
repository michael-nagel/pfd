#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import arviz as az
import matplotlib.pyplot as plt
import seaborn as sns

from pfd.utils import finalize_plot

# Function


def plot_traces(
    mod_trace: az.InferenceData, param: str, path: str, save: bool
) -> None:
    """
    Plot posterior distributions.

    Parameters
    ----------
    mod_trace : az.InferenceData
        Record of the sampling process.
    param: str
        Parameter to be plotted.
    path : str
        Path for saving.
    save : bool
        Save figure if True.
    """
    bookies_traces = mod_trace.posterior["bookmakers"].to_numpy()
    param_vals = mod_trace.posterior[param].to_numpy()

    _, ax = plt.subplots(
        nrows=len(bookies_traces), ncols=2, figsize=(6.4, 28.8)
    )
    for i, bookie in enumerate(bookies_traces):
        for c in range(0, param_vals.shape[0]):
            sns.kdeplot(
                param_vals[c, :, i].flatten(), label=bookie, ax=ax[i, 0]
            )
            ax[i, 1].plot(param_vals[c, :, i].flatten(), label=bookie)
        ax[i, 0].set(xlabel="", ylabel="", title=bookie)
        ax[i, 1].set(xlabel="", ylabel="", title=bookie)
        if param == "Phi":
            ax[i, 0].ticklabel_format(
                style="sci", scilimits=(0, 0), axis="both"
            )
            ax[i, 1].ticklabel_format(style="sci", scilimits=(0, 0), axis="y")
    finalize_plot(path=path, save=save)
