#!/usr/bin/env python3

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
from hydra.core.config_store import ConfigStore

from pfd.helpers import save_values
from pfd.utils import (
    Logger,
    NumFormat,
    PFDConfig,
    PlotParams,
    finalize_plot,
    mod_tex_tab,
    write_text_file,
)

# Hydra Setup

cs = ConfigStore.instance()
cs.store(name="pfd_config", node=PFDConfig)

# Function


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def create_descriptives(cfg: PFDConfig) -> None:
    # Logging

    log = Logger.init_logger(name=__name__)
    t_start = Logger.get_time()

    # External Files

    with open(f"{cfg.paths.acc}{cfg.files.clr_plt}") as f:
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
    # Large flat - 100%, 1x2 plots
    rcp_lf = plot_params.set_rc_params(kind="fig_big", fig_size=(6.4, 2.8))

    # Tables

    # Descriptives for numerical variables
    desc_num = df[
        ["Match", "OddsMvt", "OpnOdds", "ClsOdds", "TsDur", "NumOddsMvt"]
    ].describe()

    desc_num.loc["count", :] = desc_num.loc["count", :] / 1000000
    desc_num = desc_num.rename(index={"count": "count (in mil.)"})

    desc_num.index = desc_num.index.str.replace("%", "\\%", regex=False)

    desc_num = desc_num.rename(
        columns=dict(
            zip(
                desc_num.columns,
                [
                    "Match Outcome",
                    "Price",
                    "Op. Price",
                    "Cl. Price",
                    "Time",
                    "No. Price Changes",
                ],
                strict=True,
            )
        )
    )

    desc_num = desc_num.T

    # desc_num = desc_num.rename(
    #     columns=dict(
    #         zip(
    #             desc_num.columns,
    #             [
    #                 "$\\omega$",
    #                 "$\\bs{p}$",
    #                 "$\\bs{p}_0$",
    #                 "$\\bs{p}_T$",
    #                 "$T$",
    #                 "$C$",
    #             ],
    #         )
    #     )
    # )

    # Descriptives for categorical variables
    desc_cat = df[
        ["Bookies", "Country", "Competition", "Tournament"]
    ].describe()
    desc_cat = desc_cat.rename(columns={"Bookies": "Bookmaker"})

    desc_cat.loc["count", :] = desc_cat.loc["count", :] / 1000000
    desc_cat = desc_cat.rename(index={"count": "count (in mil.)"})
    desc_cat = desc_cat.T

    # Plotting

    pylab.rcParams.update(rcp_lf)

    # Empirical distribution of bookmakers
    _, ax = plt.subplots()
    sns.barplot(df.groupby("GroupId")["Bookies"].first().value_counts())
    ax.set(xlabel="Bookmaker", ylabel="Count")
    plt.xticks(rotation=90)
    finalize_plot(
        path=f"{cfg.paths.figures}dist_bookies.pdf", save=cfg.general.save
    )

    pylab.rcParams.update(rcp_s)

    # Empirical distribution of implied probabilities
    _, ax = plt.subplots()
    sns.histplot(
        data=df,
        x="OddsMvt",
        stat="density",
        kde=True,
        bins=25,
    )
    ax.set(xlabel="Implied Probabilities")
    finalize_plot(
        path=f"{cfg.paths.figures}dist_impl_probs.pdf",
        save=cfg.general.save,
    )

    opn_cls = pd.concat(
        objs=[df["OpnOdds"], df["ClsOdds"]], keys=["Opening", "Closing"]
    ).reset_index()
    opn_cls.columns = ["Type", "Index", "Odds"]
    opn_cls = opn_cls.drop(columns=["Index"])

    _, ax = plt.subplots()
    sns.violinplot(
        data=opn_cls,
        x="Odds",
        hue="Type",
        inner="quart",
        split=True,
        gap=0.05,
        common_norm=True,
    )
    ax.set(ylabel="Density", xlabel="Price")
    ax.legend(title="")
    finalize_plot(
        path=f"{cfg.paths.figures}violin_opn_cls.pdf",
        save=cfg.general.save,
    )

    timestamps = timestamps.dt.date

    _, ax = plt.subplots()
    sns.histplot(
        data=timestamps,
        discrete=True,
        stat="density",
        fill=True,
        edgecolor=stata_colors[0],
        alpha=1,
    )
    ax.set(xlabel="Crawling Date")
    plt.xticks(rotation=45)
    finalize_plot(
        path=f"{cfg.paths.figures}crawling_process.pdf",
        save=cfg.general.save,
    )

    _, ax = plt.subplots()
    sns.histplot(
        data=df.groupby("GroupId")["NumOddsMvt"].first(),
        bins=df["NumOddsMvt"].nunique(),
        discrete=True,
        stat="density",
        alpha=1,
    )
    ax.set(xlabel="Number of Price Movements")
    plt.xticks(np.arange(1, 21, 2))
    finalize_plot(
        path=f"{cfg.paths.figures}hist_price_mvts.pdf",
        save=cfg.general.save,
    )

    _, ax = plt.subplots()
    sns.histplot(
        data=df.groupby("GroupId")["TsDur"].first(),
        bins=int((df["TsDur"].max() - df["TsDur"].min()) * 3),
        binrange=[int(df["TsDur"].min()), int(df["TsDur"].max())],
        stat="density",
        fill=True,
        edgecolor=stata_colors[0],
        alpha=1,
    )
    ax.set(xlabel="Time Series Duration (h)")
    plt.xticks(np.linspace(df["TsDur"].min(), df["TsDur"].max(), 6, dtype=int))
    finalize_plot(
        path=f"{cfg.paths.figures}hist_ts_dur.pdf",
        save=cfg.general.save,
    )

    # Saving

    save_values(
        key="ts_dur_med",
        value=desc_num.loc["Time", "50\\%"],
        file_name=f"{cfg.paths.vals}{cfg.files.vals}",
        fmt=".2f",
    )

    write_text_file(
        file=f"{cfg.paths.tables}desc_num.tex",
        body=mod_tex_tab(
            tab=desc_num.apply(NumFormat.format_col)
            .style.format(
                na_rep="",
            )
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
