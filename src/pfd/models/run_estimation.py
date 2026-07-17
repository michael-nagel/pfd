#!/usr/bin/env python3

"""
This file runs the estimation procedure.
"""

# Imports

import json

import hydra
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from hydra.core.config_store import ConfigStore

from pfd.helpers import save_values
from pfd.models.bayesian_estimation import estimate_bayesian_learning_rate
from pfd.models.bookmaker_accuracy import analyze_bookmaker_accuracy
from pfd.models.filter_and_shape import filter_and_shape_data
from pfd.models.gmm_estimation import estimate_gmm_learning_rate
from pfd.models.resample_and_impute import resample_and_impute_data
from pfd.models.time_series_diagnostics import analyze_time_series_diagnostics
from pfd.models.unbiasedness_regressions import (
    estimate_unbiasedness_regressions,
)
from pfd.models.winning_proportions import analyze_winning_proportions
from pfd.utils import (
    Logger,
    NumFormat,
    PFDConfig,
    PlotParams,
    mod_tex_tab,
    write_text_file,
)

# Hydra Setup

cs = ConfigStore.instance()
cs.store(name="pfd_config", node=PFDConfig)

# Function


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def run_estimation(cfg: PFDConfig) -> None:
    # Logging

    log = Logger.init_logger(name=__name__)
    t_start = Logger.get_time()

    # External Files

    with open(f"{cfg.paths.acc}{cfg.files.clr_plt}") as f:
        stata_colors = json.load(f)

    with open(f"{cfg.paths.acc}{cfg.files.clr_plt_ext}") as f:
        stata_colors_ext = json.load(f)

    stata_colors = stata_colors + stata_colors_ext

    df = pd.read_hdf(
        path_or_buf=f"{cfg.paths.data_proc}shaped_data.h5",
        key="df",
    )

    # Cockpit

    np.random.seed(cfg.general.seed)

    plt.close("all")
    sns.set_theme(palette=stata_colors, style="ticks")

    plot_params = PlotParams(cfg=cfg)

    # Shaping, estimation and descriptive analyses

    df, df_desc, bookies, exog_cols, n_obs, n_groups, is_amateur, is_pro = (
        filter_and_shape_data(df=df, cfg=cfg)
    )

    rmse, df_oc, iqr_rtrns, tex_res_gpm, tex_res_rfa, df_res_rfa = (
        analyze_bookmaker_accuracy(
            df=df,
            exog_cols=exog_cols,
            bookies=bookies,
            cfg=cfg,
            plot_params=plot_params,
            stata_colors=stata_colors,
        )
    )

    res_win_props, tex_res_wp_re, bootstr_std, bootstr_low, bootstr_up = (
        analyze_winning_proportions(
            df_oc=df_oc,
            bookies=bookies,
            cfg=cfg,
            plot_params=plot_params,
            stata_colors=stata_colors,
        )
    )

    df, odds_mvt_cols, n_per, frac_missings = resample_and_impute_data(
        df=df, exog_cols=exog_cols, cfg=cfg, plot_params=plot_params
    )

    adf_stat, adf_p, tex_res_garch = analyze_time_series_diagnostics(
        df=df,
        exog_cols=exog_cols,
        odds_mvt_cols=odds_mvt_cols,
        n_per=n_per,
        cfg=cfg,
        plot_params=plot_params,
        stata_colors=stata_colors,
    )

    signific_time_idx = estimate_unbiasedness_regressions(
        df=df, odds_mvt_cols=odds_mvt_cols, cfg=cfg, plot_params=plot_params
    )

    gamma_stats_gmm, idxmin_gamma_gmm, idxmax_gamma_gmm = (
        estimate_gmm_learning_rate(
            df=df,
            n_per=n_per,
            bookies=bookies,
            cfg=cfg,
            plot_params=plot_params,
            stata_colors=stata_colors,
        )
    )

    (
        res_pm,
        metrics,
        gamma_med_nuts,
        gamma_lower_nuts,
        gamma_upper_nuts,
        gamma_fav,
        gamma_udd,
        gamma_pro,
        gamma_amat,
    ) = estimate_bayesian_learning_rate(
        df=df,
        n_per=n_per,
        rmse=rmse,
        cfg=cfg,
        plot_params=plot_params,
        stata_colors=stata_colors,
    )

    # Saving

    if cfg.general.save:
        # DataFrames
        df_desc.to_hdf(
            path_or_buf=f"{cfg.paths.data_proc}data_desc.h5",
            key="data_desc",
            mode="w",
        )

        # TODO
        with open(
            f"{cfg.paths.data_proc}rmse.json", "w", encoding="utf-8"
        ) as f:
            json.dump(
                rmse.sort_values().to_dict(), f, ensure_ascii=False, indent=4
            )

        with open(
            f"{cfg.paths.data_proc}signific_time_idx.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                signific_time_idx.tolist(), f, ensure_ascii=False, indent=4
            )

        metrics.to_hdf(
            path_or_buf=f"{cfg.paths.data_proc}metrics.h5",
            key="metrics",
            mode="w",
        )

        # Values
        values_to_save = {
            "bm_quantile": (cfg.estimation.bm_quantile * 100, ".0f"),
            "ts_dur_from": (cfg.estimation.ts_dur[0], None),
            "ts_dur_till": (cfg.estimation.ts_dur[1], None),
            "iqr_rtrns": (iqr_rtrns, ".4f"),
            "n_obs": (n_obs, ","),
            "n_groups": (n_groups, None),
            "gamma_med_nuts": (gamma_med_nuts, ".4f"),
            "gamma_fav": (gamma_fav, ".4f"),
            "gamma_udd": (gamma_udd, ".4f"),
            "gamma_pro": (gamma_pro, ".4f"),
            "gamma_amat": (gamma_amat, ".4f"),
            "gamma_lower_nuts": (gamma_lower_nuts, ".4f"),
            "gamma_upper_nuts": (gamma_upper_nuts, ".4f"),
            "is_amateur": (is_amateur, ".4f"),
            "is_pro": (is_pro, ".4f"),
            # "n_missings": (n_missings, None),
            "frac_missings": (frac_missings, ".4f"),
            "n_per": (n_per, ".0f"),
            "avg_gamma_gmm": (gamma_stats_gmm["mean"], ".4f"),
            "min_gamma_gmm": (gamma_stats_gmm["min"], ".4f"),
            "max_gamma_gmm": (gamma_stats_gmm["max"], ".4f"),
            "idxmax_gamma_gmm": (idxmax_gamma_gmm, None),
            "idxmin_gamma_gmm": (idxmin_gamma_gmm, None),
            "adf_stat": (adf_stat, ".2f"),
            "adf_p": (adf_p, ".4f"),
            "corr_gamma_loss": (
                metrics["RMSE"].corr(metrics["Learning Rate"]),
                ".4f",
            ),
            "bootstr_std": (bootstr_std[0], ".4f"),
            "bootstr_up": (bootstr_up[0], ".4f"),
            "bootstr_low": (bootstr_low[0], ".4f"),
        }

        for key, (value, fmt) in values_to_save.items():
            save_values(
                key=key,
                value=value,
                file_name=f"{cfg.paths.vals}{cfg.files.vals}",
                fmt=fmt,
            )

        # Sampling parameters from config.yaml
        for key, value in cfg.sampling.items():
            save_values(
                key=key,
                value=value,
                file_name=f"{cfg.paths.vals}{cfg.files.vals}",
            )

        # Tables
        file_configs = [
            (f"{cfg.paths.tables}res_gpm.tex", "".join(tex_res_gpm)),
            (f"{cfg.paths.tables}res_rfa.tex", "".join(tex_res_rfa)),
            (f"{cfg.paths.tables}res_wp_re.tex", "".join(tex_res_wp_re)),
            (f"{cfg.paths.tables}res_garch.tex", "".join(tex_res_garch)),
        ]

        for file, body in file_configs:
            write_text_file(
                file=file, body=body, first_line=None, last_line=None
            )

        # Further tables
        write_text_file(
            file=f"{cfg.paths.tables}res_rfa_tot.tex",
            body=mod_tex_tab(
                tab=df_res_rfa.apply(NumFormat.format_col)
                .style.format(na_rep="")
                .to_latex()
            ),
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_wp.tex",
            body=mod_tex_tab(
                tab=res_win_props["All"]
                .apply(NumFormat.format_col)
                .style.hide(axis="index")
                .format(na_rep="")
                .to_latex()
            ),
        )

        write_text_file(
            file=f"{cfg.paths.tables}res_pm_mod.tex",
            body=mod_tex_tab(
                tab=res_pm["nuts_tot"]["sum"]
                .apply(NumFormat.format_col)
                .style.format(
                    formatter={
                        r"$\hat{R}$": NumFormat(my_format="{:.2f}").format_post
                    },
                    na_rep="NaN",
                )
                .to_latex()
            ),
        )

    # Execution Time and Log File Finish

    log.info(f"Execution time: {Logger.get_exec_time(start_time=t_start)}")


if __name__ == "__main__":
    run_estimation()
