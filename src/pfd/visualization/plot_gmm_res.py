#!/usr/bin/env python3

# Imports


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

from pfd.utils import finalize_plot

# %% Function


def plot_gmm_res(
    res_gmm: dict[str, list],
    bookies: list,
    edgecolor: str,
    paths: list[str],
    save: bool,
) -> None:
    """
    Plot GMM results.

    Parameters
    ----------
    res_gmm : Dict[str, list]
        Dictionary that contains the GMM results.
    bookies: list
        Bookmakers.
    edgecolor: str
        Edgecolor for markers.
    paths : List
        List of paths for saving.
    save : bool
        Save figure if True.
    """

    df_res_gmm_first_stage = pd.DataFrame(
        data=[ele[0] for ele in res_gmm["first_stage"]], index=bookies
    )
    df_res_gmm_cue = pd.DataFrame(
        data=[ele[0] for ele in res_gmm["cue"]], index=bookies
    )

    _, ax = plt.subplots(nrows=2, ncols=1, sharex="all", sharey="all")
    ax[0].errorbar(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm_first_stage["gamma"],
        yerr=df_res_gmm_first_stage["std_gamma"] * norm.ppf(0.975),
        fmt="o",
        markerfacecolor="none",
        capsize=5,
        lw=1,
    )
    ax[0].hlines(y=0, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[0].set(title="First-Stage GMM", ylabel="Learning Rate")
    ax[1].errorbar(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm_cue["gamma"],
        yerr=df_res_gmm_cue["std_gamma"] * norm.ppf(0.975),
        fmt="o",
        markerfacecolor="none",
        capsize=5,
        lw=1,
    )
    ax[1].hlines(y=0, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[1].set(
        title="CUE",
        ylabel="Learning Rate",
        xlabel="Bookmaker",
    )
    ax[1].set_xticks(np.arange(0, len(bookies)), bookies, rotation=90)
    finalize_plot(path=paths[0], save=save)

    _, ax = plt.subplots(nrows=2, ncols=1, sharex="all", sharey="all")
    ax[0].scatter(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm_first_stage["J_stat"],
        facecolor="none",
        edgecolor=edgecolor,
    )
    ax[0].set(title="First-Stage GMM", ylabel="J-statistic")
    ax[1].scatter(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm_cue["J_stat"],
        facecolor="none",
        edgecolor=edgecolor,
    )
    ax[1].set(
        title="CUE",
        xlabel="Bookmaker",
        ylabel="J-statistic",
    )
    ax[1].set_xticks(np.arange(0, len(bookies)), bookies, rotation=90)
    finalize_plot(path=paths[1], save=save)

    _, ax = plt.subplots(nrows=2, ncols=1, sharex="all", sharey="all")
    ax[0].scatter(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm_first_stage["p_value"],
        facecolor="none",
        edgecolor=edgecolor,
    )
    ax[0].hlines(y=0.05, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[0].set_ylim(bottom=0)
    ax[0].set(
        title="First-Stage GMM",
        ylabel="p-value",
    )
    ax[1].scatter(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm_cue["p_value"],
        facecolor="none",
        edgecolor=edgecolor,
    )
    ax[1].hlines(y=0.05, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[1].set_ylim(bottom=0)
    ax[1].set(
        title="CUE",
        xlabel="Bookmaker",
        ylabel="p-value",
    )
    ax[1].set_xticks(np.arange(0, len(bookies)), bookies, rotation=90)
    finalize_plot(path=paths[2], save=save)
