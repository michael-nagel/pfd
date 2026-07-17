#!/usr/bin/env python3

# Imports

import matplotlib.pyplot as plt
import numpy as np
from omegaconf import DictConfig
from scipy.stats import norm

from pfd.utils import finalize_plot

# %% Function


def plot_unbiased_reg_res(
    res_ur: dict[str, list[float]], cfg: DictConfig, path: str, save: bool
) -> None:
    """
    Plot unbiasedness regression results.

    Parameters
    ----------
    res_ur : dict[str, list[float]]
        Dict that contains the unbiasedness regressions results.
    cfg : DictConfig
        Dictionary containing config parameters.
    path : str
        Path for saving.
    save : bool
        Save figure if True.
    """
    pctl = cfg.estimation.pctl

    fig, ax = plt.subplots(nrows=2, ncols=1, sharex="all", sharey="none")
    ax[0].plot(np.arange(0, len(res_ur["beta_1"])), res_ur["beta_1"])
    ax[0].fill_between(
        x=np.arange(0, len(res_ur["beta_1"])),
        y1=np.array(res_ur["beta_1"])
        + norm.ppf(0.975) * np.array(res_ur["std_beta_1"]),
        y2=np.array(res_ur["beta_1"])
        - norm.ppf(0.975) * np.array(res_ur["std_beta_1"]),
        alpha=0.15,
    )
    ax[0].hlines(
        y=1, xmin=0, xmax=len(res_ur["beta_1"]) - 1, linestyles="dotted"
    )
    ax[0].set(xlabel="", ylabel="Slope")
    ax[0].set_xticks(
        np.arange(0, len(res_ur["rmse"]))[::6],
        np.arange(pctl, 100 + pctl, pctl)[::6],
    )
    # ax[0].set_ylim(bottom=0)
    ax[1].plot(np.arange(0, len(res_ur["rmse"])), res_ur["rmse"])
    ax[1].set(xlabel="Percentile Time Increments", ylabel="RMSE")
    ax[1].set_xticks(
        np.arange(0, len(res_ur["rmse"]))[::6],
        np.arange(pctl, 100 + pctl, pctl)[::6],
    )
    finalize_plot(path=path, save=save)
