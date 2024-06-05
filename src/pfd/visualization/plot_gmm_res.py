#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import norm

from pfd.utils import finalize_plot

# %% Function


def plot_gmm_res(
    res_gmm: list, bookies: list, edgecolor: str, paths: list, save: bool
) -> None:
    """
    Plot GMM results.

    Parameters
    ----------
    res_gmm : list
        List that contains the GMM results.
    bookies: list
        Bookmakers.
    edgecolor: str
        Edgecolor for markers.
    paths : list
        List of paths for saving.
    save : bool
        Save figure if True.
    """

    df_res_gmm = pd.DataFrame(data=[ele[0] for ele in res_gmm], index=bookies)

    gamma_tot = np.array(
        [[sub_ele["gamma"] for sub_ele in ele] for ele in res_gmm]
    ).T
    phi_tot = np.array(
        [[sub_ele["Phi"] for sub_ele in ele] for ele in res_gmm]
    ).T

    _, ax = plt.subplots(nrows=2, ncols=1, sharex="all")
    ax[0].errorbar(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm["gamma"],
        yerr=df_res_gmm["std_gamma"] * norm.ppf(0.975),
        fmt="o",
        markerfacecolor="none",
        capsize=5,
        lw=1,
    )
    ax[0].hlines(y=0, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[0].set(ylabel=r"$\hat{\gamma}$")
    ax[0].set_xticks(np.arange(0, len(bookies)), bookies, rotation=90)
    ax[1].errorbar(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm["Phi"],
        yerr=df_res_gmm["std_Phi"] * norm.ppf(0.975),
        fmt="o",
        markerfacecolor="none",
        capsize=5,
        lw=1,
    )
    ax[1].hlines(y=0, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[1].set(xlabel="Bookmaker", ylabel=r"$\hat{\Phi}$")
    ax[1].set_xticks(np.arange(0, len(bookies)), bookies, rotation=90)
    finalize_plot(path=paths[0], save=save)

    _, ax = plt.subplots(nrows=2, ncols=1, sharex="all")
    ax[0].scatter(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm["J_stat"],
        facecolor="none",
        edgecolor=edgecolor,
    )
    ax[0].set(ylabel="$J$")
    ax[0].set_xticks(np.arange(0, len(bookies)), bookies, rotation=90)
    ax[1].scatter(
        x=np.arange(0, len(bookies)),
        y=df_res_gmm["p_value"],
        facecolor="none",
        edgecolor=edgecolor,
    )
    ax[1].hlines(y=0.05, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[1].set(xlabel="Bookmaker", ylabel="p-value")
    ax[1].set_xticks(np.arange(0, len(bookies)), bookies, rotation=90)
    finalize_plot(path=paths[1], save=save)

    _, ax = plt.subplots(nrows=2, ncols=1, sharex="all")
    sns.boxplot(data=gamma_tot, ax=ax[0], showfliers=False)
    ax[0].hlines(y=0, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[0].set(ylabel=r"$\hat{\gamma}$")
    sns.boxplot(data=phi_tot, ax=ax[1], showfliers=False)
    ax[1].hlines(y=0, xmin=0, xmax=len(bookies) - 1, linestyles="dotted")
    ax[1].set(xlabel="Bookmaker", ylabel=r"$\hat{\Phi}$")
    ax[1].set_xticks(np.arange(0, len(bookies)), bookies, rotation=90)
    finalize_plot(path=paths[2], save=save)
