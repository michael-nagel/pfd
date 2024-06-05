#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file creates descriptive statistics.
"""

# Imports

import json

import hydra
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from hydra import compose, initialize
from hydra.core.config_store import ConfigStore

from pfd.utils import (
    Logger,
    NumFormat,
    PFDConfig,
    PlotParams,
    calc_losses,
    finalize_plot,
    mod_tex_tab,
    write_text_file,
)

# Hydra Setup

cs = ConfigStore.instance()
cs.store(name="pfd_config", node=PFDConfig)

# Function

with initialize(
    version_base=None, config_path="../conf", job_name="run_descriptives"
):
    cfg = compose(config_name="config")


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def create_descriptives(cfg: PFDConfig) -> None:
    # Logging

    log = Logger.init_logger(name=__name__)
    t_start = Logger.get_time()

    # External Files

    with open(f"{cfg.paths.acc}{cfg.files.clr_plt}", "r") as f:
        stata_colors = json.load(f)

    df = pd.read_hdf(path_or_buf=f"{cfg.paths.data_proc}data_desc.h5")

    timestamps = pd.read_hdf(path_or_buf=f"{cfg.paths.data_proc}timestamps.h5")

    # Cockpit

    np.random.seed(cfg.general.seed)

    plt.close("all")
    sns.set_theme(palette=stata_colors, style="ticks")

    plot_params = PlotParams(cfg=cfg)
    # 50%, single plots
    rcp_s = plot_params.set_rc_params(kind="fig_small", fig_size=(6.4, 4.8))
    # 75%, 2x1 and 2x2 plots
    rcp_m = plot_params.set_rc_params(kind="fig_medium", fig_size=(6.4, 4.8))

    # Tables

    desc_num = df[
        ["Match", "OddsMvt", "OpnOdds", "ClsOdds", "TsDur", "NumOddsMvt"]
    ].describe()

    desc_num.index = desc_num.index.str.replace("%", "\\%", regex=False)
    desc_num = desc_num.rename(
        columns=dict(
            zip(
                desc_num.columns,
                ["$\\omega$", "$\\mathbf{Q}$", "$Q_1$", "$Q_T$", "$T$", "$C$"],
            )
        )
    )

    desc_cat = df[
        ["Bookies", "Country", "Competition", "Tournament"]
    ].describe()
    desc_cat = desc_cat.rename(columns={"Bookies": "Bookmaker"})

    # Plotting

    metrics = df.groupby("Bookies").apply(calc_losses, include_groups=False)
    metrics = pd.DataFrame(
        metrics.tolist(), columns=["BrierLoss", "LogLoss"], index=metrics.index
    )

    pylab.rcParams.update(rcp_m)

    _, ax = plt.subplots(nrows=2, ncols=1, sharex="all", sharey="none")
    sns.barplot(data=metrics, x=metrics.index, y="BrierLoss", ax=ax[0])
    ax[0].set(xlabel="", ylabel="Brier Score Loss")
    sns.barplot(data=metrics, x=metrics.index, y="LogLoss", ax=ax[1])
    ax[1].set(xlabel="Bookmaker", ylabel="Log Loss")
    plt.xticks(np.arange(0, len(metrics.index)), metrics.index, rotation=90)
    finalize_plot(
        path=f"{cfg.paths.figures}log_brier_loss.pdf", save=cfg.general.save
    )

    timestamps = pd.to_datetime(timestamps, errors="coerce")
    timestamps = timestamps.dt.date

    pylab.rcParams.update(rcp_s)

    _, ax = plt.subplots()  # TODO title: crawling process density
    sns.histplot(data=timestamps, discrete=True, stat="density")
    ax.set(xlabel="Crawling Date")
    plt.xticks(rotation=45)
    finalize_plot(
        path=f"{cfg.paths.figures}crawling_process.png",
        save=cfg.general.save,
        fmt="png",
    )

    exem_match = df.loc[
        (df["NumOddsMvt"] == 20) & (df["TsDur"] > 12) & (df["TsDur"] < 24)
    ].copy()
    exem_match = exem_match.loc[
        exem_match["GroupId"] == exem_match["GroupId"].min(), :
    ]
    exem_match["Time"] = pd.to_datetime(exem_match["Update"]).dt.strftime(
        "%H:%M"
    )
    exem_match = exem_match.set_index(["Time"])

    _, ax = plt.subplots()
    ax.plot(exem_match.index, exem_match["OddsMvt"])
    ax.set(xlabel="Update", ylabel="Implied Probability")
    plt.xticks(rotation=45)
    finalize_plot(
        path=f"{cfg.paths.figures}ts_exem_match.pdf", save=cfg.general.save
    )

    _, ax = plt.subplots()
    sns.histplot(
        data=df.groupby("GroupId")["NumOddsMvt"].first(),
        bins=df["NumOddsMvt"].nunique(),
        discrete=True,
        stat="density",
    )
    ax.set(xlabel="Number of Odds Movements")
    plt.xticks(np.arange(1, 21, 1))
    finalize_plot(
        path=f"{cfg.paths.figures}hist_odds_mvts.pdf",
        save=cfg.general.save,
    )

    _, ax = plt.subplots()
    sns.histplot(
        data=df.groupby("GroupId")["TsDur"].first(),
        bins=int((df["TsDur"].max() - df["TsDur"].min()) * 3),
        binrange=[int(df["TsDur"].min()), int(df["TsDur"].max())],
        stat="density",
    )
    ax.set(xlabel="Time Series Duration (h)")
    plt.xticks(np.linspace(df["TsDur"].min(), df["TsDur"].max(), 6, dtype=int))
    finalize_plot(
        path=f"{cfg.paths.figures}hist_ts_dur.png",
        save=cfg.general.save,
        fmt="png",
    )

    # Saving

    write_text_file(
        file=f"{cfg.paths.tables}desc_num.tex",
        body=mod_tex_tab(
            tab=desc_num.map(NumFormat.format_num)
            .style.format(na_rep="")
            .to_latex()
        ),
    )

    write_text_file(
        file=f"{cfg.paths.tables}desc_cat.tex",
        body=mod_tex_tab(
            tab=desc_cat.apply(NumFormat.format_col)
            .style.format(na_rep="")
            .to_latex()
        ),
    )

    # Execution Time and Log File Finish

    log.info(f"Execution time: {Logger.get_exec_time(start_time=t_start)}")


if __name__ == "__main__":
    create_descriptives()
