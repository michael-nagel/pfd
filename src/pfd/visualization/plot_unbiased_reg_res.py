#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import matplotlib.pyplot as plt
import numpy as np
from omegaconf import DictConfig
from scipy.stats import norm

from pfd.utils import finalize_plot

# %% Function


def plot_unbiased_reg_res(
    res_ur: list, cfg: DictConfig, path: str, save: bool
) -> None:
    """
    Plot unbiasedness regression results.

    Parameters
    ----------
    res_ur : list
        List that contains the unbiasedness regressions results.
    cfg : DictConfig
        Dictionary containing config parameters.
    path : str
        Path for saving.
    save : bool
        Save figure if True.
    """
    pctl = cfg.estimation.pctl

    fig = plt.figure()
    intcp_ax = fig.add_subplot(221)
    rmse_ax = fig.add_subplot(222)
    slope_ax = fig.add_subplot(212)
    intcp_ax.plot(np.arange(0, len(res_ur["beta_0"])), res_ur["beta_0"])
    intcp_ax.fill_between(
        x=np.arange(0, len(res_ur["beta_0"])),
        y1=np.array(res_ur["beta_0"])
        + norm.ppf(0.975) * np.array(res_ur["std_beta_0"]),
        y2=np.array(res_ur["beta_0"])
        - norm.ppf(0.975) * np.array(res_ur["std_beta_0"]),
        alpha=0.15,
    )
    intcp_ax.hlines(
        y=0, xmin=0, xmax=len(res_ur["beta_0"]) - 1, linestyles="dotted"
    )
    intcp_ax.set(xlabel="", ylabel="Intercept")
    intcp_ax.set_xticks(
        np.arange(0, len(res_ur["rmse"]))[::6],
        np.arange(pctl, 100 + pctl, pctl)[::6],
    )
    # intcp_ax.set_xticks(
    #     np.arange(0, len(res_ur["beta_0"]))[::4],
    #     np.flip(np.arange(0, len(res_ur["beta_0"])))[::4] * len_per + len_per,
    # )
    rmse_ax.plot(np.arange(0, len(res_ur["rmse"])), res_ur["rmse"])
    rmse_ax.set(xlabel="", ylabel="RMSE")
    rmse_ax.set_xticks(
        np.arange(0, len(res_ur["rmse"]))[::6],
        np.arange(pctl, 100 + pctl, pctl)[::6],
    )
    # rmse_ax.set_xticks(
    #     np.arange(0, len(res_ur["rmse"]))[::4],
    #     np.flip(np.arange(0, len(res_ur["rmse"])))[::4] * len_per + len_per,
    # )
    slope_ax.plot(np.arange(0, len(res_ur["beta_1"])), res_ur["beta_1"])
    slope_ax.fill_between(
        x=np.arange(0, len(res_ur["beta_1"])),
        y1=np.array(res_ur["beta_1"])
        + norm.ppf(0.975) * np.array(res_ur["std_beta_1"]),
        y2=np.array(res_ur["beta_1"])
        - norm.ppf(0.975) * np.array(res_ur["std_beta_1"]),
        alpha=0.15,
    )
    slope_ax.hlines(
        y=1, xmin=0, xmax=len(res_ur["beta_1"]) - 1, linestyles="dotted"
    )
    slope_ax.set(xlabel="Percentile Time Increments", ylabel="Slope")
    slope_ax.set_xticks(
        np.arange(0, len(res_ur["rmse"]))[::6],
        np.arange(pctl, 100 + pctl, pctl)[::6],
    )
    plt.ylim(bottom=0)
    # slope_ax.set_xticks(
    #     np.arange(0, len(res_ur["beta_1"]))[::4],
    #     np.flip(np.arange(0, len(res_ur["beta_1"])))[::4] * len_per + len_per,
    # )
    finalize_plot(path=path, save=save)
