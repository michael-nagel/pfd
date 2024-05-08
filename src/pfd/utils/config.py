# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import os
from dataclasses import dataclass
from pathlib import Path

# Classes


@dataclass
class Paths:
    acc: str
    data_ext: str
    data_intrm: str
    data_proc: str
    data_raw: str
    models: str
    figures: str
    tables: str
    vals: str

    def __post_init__(self):
        """
        Validate input paths.

        Validate the input paths to ensure they are valid file system paths.
        """
        for attr in self.__annotations__:
            path = getattr(self, attr)
            if not Path(path).is_dir():
                raise ValueError(f"Invalid path: {path}")

    def create_directories(self) -> None:
        """
        Create the directories if they do not exist.
        """
        os.makedirs(self.acc, exist_ok=True)
        os.makedirs(self.data_ext, exist_ok=True)
        os.makedirs(self.data_intrm, exist_ok=True)
        os.makedirs(self.data_proc, exist_ok=True)
        os.makedirs(self.data_raw, exist_ok=True)
        os.makedirs(self.models, exist_ok=True)
        os.makedirs(self.figures, exist_ok=True)
        os.makedirs(self.tables, exist_ok=True)
        os.makedirs(self.vals, exist_ok=True)


@dataclass
class Files:
    clr_plt: str
    chrm_driv: str
    acpt_cookies: str
    cred: str
    vals: str

    def __post_init__(self):
        if not isinstance(self.clr_plt, str):
            raise TypeError("clr_plt must be a string")


@dataclass
class General:
    seed: int
    save: bool
    main_scripts: list

    def __post_init__(self):
        if not isinstance(self.seed, int):
            raise TypeError("seed must be an integer")
        if not isinstance(self.save, bool):
            raise TypeError("save must be a boolean")
        if not isinstance(self.main_scripts, list):
            raise TypeError("main_scripts must be a list")


@dataclass
class Scraping:
    headless: bool
    crawl_till: str
    repeat_per: int
    sleep: int

    def __post_init__(self):
        if not isinstance(self.headless, int):
            raise TypeError("headless must be an integer")
        if not isinstance(self.crawl_till, bool):
            raise TypeError("crawl_till must be a boolean")
        if not isinstance(self.repeat_per, int):
            raise TypeError("repeat_per must be an integer")
        if not isinstance(self.sleep, int):
            raise TypeError("sleep must be an integer")


@dataclass
class Estimation:
    spec: str
    compets: None | list
    bm_quantile: float
    odds_mvmnts: list
    ts_dur: list
    period: float | None
    resample_freq: str
    incr: int
    start_params: list
    max_iter: int | str

    def __post_init__(self):
        if not isinstance(self.spec, str):
            raise TypeError("spec must be a string")
        if not isinstance(self.compets, (str, None)):
            raise TypeError("compets must be a string or NoneType")
        if not isinstance(self.bm_quantile, float):
            raise TypeError("bm_quantile must be a float")
        if not isinstance(self.odds_mvmnts, list):
            raise TypeError("odds_mvmnts must be a list")
        if not isinstance(self.ts_dur, list):
            raise TypeError("ts_dur must be a list")
        if not isinstance(self.period, (float, None)):
            raise TypeError("period must be a float or NoneType")
        if self.period is not None and self.ts_dur[0] < self.period:
            raise ValueError("ts_dur[0] must be larger or equal than period")
        if not isinstance(self.resample_freq, str):
            raise TypeError("resample_freq must be a string")
        if not isinstance(self.incr, str):
            raise TypeError("incr must be an integer")
        if not isinstance(self.start_params, list):
            raise TypeError("start_params must be a list")
        if not isinstance(self.max_iter, (int, str)):
            raise TypeError("max_iter must be an integer or string")


@dataclass
class Sampling:
    hdi: float
    n_chains: int
    n_draws: int
    n_tune: int
    n_cores: int
    targ_acpt: float
    vi_n_iter: int
    vi_n_draws: int

    def __post_init__(self):
        if not isinstance(self.hdi, float):
            raise TypeError("hdi must be a float")
        if not isinstance(self.n_chains, int):
            raise TypeError("n_chains must be an integer")
        if not isinstance(self.n_draws, int):
            raise TypeError("n_draws must be an integer")
        if not isinstance(self.n_tune, int):
            raise TypeError("n_tune must be an integer")
        if not isinstance(self.n_cores, int):
            raise TypeError("n_cores must be an integer")
        if not isinstance(self.targ_acpt, float):
            raise TypeError("targ_acpt must be a float")
        if not isinstance(self.vi_n_iter, int):
            raise TypeError("vi_n_iter must be an integer")
        if not isinstance(self.vi_n_draws, int):
            raise TypeError("vi_n_draws must be an integer")


@dataclass
class Plotting:
    base_siz: float
    leg_mkr_siz: float
    line_width: float
    mkr_siz: float
    ax_line_width: float
    xtick_maj_width: float
    ytick_maj_width: float
    xtick_maj_siz: float
    ytick_maj_siz: float
    font_family: str

    def __post_init__(self):
        if not isinstance(self.base_siz, float):
            raise TypeError("base_siz must be a float")
        if not isinstance(self.leg_mkr_siz, float):
            raise TypeError("leg_mkr_siz must be a float")
        if not isinstance(self.line_width, float):
            raise TypeError("line_width must be a float")
        if not isinstance(self.mkr_siz, float):
            raise TypeError("mkr_siz must be a float")
        if not isinstance(self.ax_line_width, float):
            raise TypeError("ax_line_width must be a float")
        if not isinstance(self.xtick_maj_width, float):
            raise TypeError("xtick_maj_width must be a float")
        if not isinstance(self.ytick_maj_width, float):
            raise TypeError("ytick_maj_width must be a float")
        if not isinstance(self.xtick_maj_siz, float):
            raise TypeError("xtick_maj_siz must be a float")
        if not isinstance(self.ytick_maj_siz, float):
            raise TypeError("ytick_maj_siz must be a float")
        if not isinstance(self.font_family, str):
            raise TypeError("font_family must be a string")


@dataclass
class PFDConfig:
    paths: Paths
    files: Files
    general: General
    scraping: Scraping
    estimation: Estimation
    sampling: Sampling
    plotting: Plotting
