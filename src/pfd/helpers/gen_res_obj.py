# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from typing import Any, Tuple

import arviz as az
import numpy as np
import pandas as pd
from omegaconf import DictConfig

from pfd.helpers.base import create_pm_mod
from pfd.utils import est_pm_mod

# Function


def gen_res_obj(
    df: pd.DataFrame, est_method: str, subset: str, n_per: int, cfg: DictConfig
) -> Tuple[Any, Any, Any] | az.InferenceData:
    """
    Generate the result objects for ADVI and NUTS.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    est_method : str
        Estimation method ("advi" or "nuts").
    subset : str
        Which subset of the data should be used for estimation.
        Possible arguments are [tot, fav, udd, pro, amat].
    n_per : int
        Number of periods
    cfg : DictConfig
        Dictionary that contains the config parameters.

    Returns
    -------
    Tuple[Any, Any, Any] | az.InferenceData
        Results for either ADVI or NUTS.
    """
    # if subset not in ["tot", "fav", "udd", "pro", "amat"]:
    #     raise ValueError("subset must be 'tot', 'pro' or 'amat'")

    if subset == "pro":
        df = df.loc[df["IsPro"] == 1]
    elif subset == "amat":
        df = df.loc[df["IsPro"] == 0]
    elif subset == "fav":
        df = df.loc[df["IsFav"] == 1]
    elif subset == "udd":
        df = df.loc[df["IsFav"] == 0]
    elif subset.startswith("q"):
        df = df.loc[df["Quantile"] == int(subset[1:])]
    else:
        pass

    model = create_pm_mod(df=df, n_per=n_per, incr=cfg.estimation.incr)

    if est_method == "advi":
        trace, tracker, advi = est_pm_mod(
            model=model,
            seed=cfg.general.seed,
            vi=True,
            vi_n_iter=cfg.sampling.vi_n_iter,
            vi_n_draws=cfg.sampling.vi_n_draws,
        )

        np.save(
            file=f"{cfg.paths.models}tracker_mean.npy", arr=tracker["mean"]
        )
        np.save(file=f"{cfg.paths.models}tracker_std.npy", arr=tracker["std"])
        np.save(file=f"{cfg.paths.models}advi_hist.npy", arr=advi.hist)

        return trace, tracker, advi

    elif est_method == "nuts":
        trace = est_pm_mod(
            model=model,
            seed=cfg.general.seed,
            n_draws=cfg.sampling.n_draws,
            n_tune=cfg.sampling.n_tune,
            n_chains=cfg.sampling.n_chains,
            n_cores=cfg.sampling.n_cores,
            targ_acpt=cfg.sampling.targ_acpt,
        )

    else:
        raise ValueError("est_method must be either 'advi' or 'nuts'")

    trace.to_netcdf(
        filename=f"{cfg.paths.models}trace_{est_method}_{subset}.nc"
    )

    return trace
