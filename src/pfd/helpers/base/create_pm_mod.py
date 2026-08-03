#!/usr/bin/env python3

# Imports

import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt

from pfd.utils import _create_gmm_data

# Function


def create_pm_mod(df: pd.DataFrame, n_per: int, incr: int) -> pm.Model:
    """
    Create PyMC model.

    This function creates the PyMC model for estimation.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    nper : int
        Number of periods.
    incr : int
        Incremental step for periods

    Returns
    -------
    pm.Model
        PyMC model to be numerically estimated.
    """
    endog, exog, inst = _create_gmm_data(df=df, n_per=n_per, incr=incr)

    bookie_idx, bookies = pd.factorize(df["Bookies"])
    coords = {
        "bookmakers": bookies,
        "obs_id": np.arange(0, len(bookie_idx)),
        "moment": np.arange(14),
    }

    with pm.Model(coords=coords) as model:
        # Mutable data
        bookie_idx = pm.MutableData(
            name="bookie_idx",
            value=bookie_idx,
            dims="obs_id",
            infer_dims_and_coords=True,
        )
        endog = pm.MutableData(
            name="endog",
            value=endog,
            dims="obs_id",
            infer_dims_and_coords=True,
        )
        exog = pm.MutableData(
            name="exog",
            value=exog[:, 0:3],
            dims=("obs_id", "exogenous"),
            infer_dims_and_coords=True,
        )
        inst = pm.MutableData(
            name="inst",
            value=inst,
            dims=("obs_id", "instruments"),
            infer_dims_and_coords=True,
        )

        # Model error
        sd_eps = pm.HalfCauchy(name="sd_eps", beta=0.01)

        # Random effects gamma
        mean_gamma = pm.Truncated(
            name="mean_gamma",
            dist=pm.Normal.dist(mu=0, sigma=1),
            lower=0,
        )
        sd_gamma = pm.Exponential(name="sd_gamma", lam=2.5)
        gamma = pm.Truncated(
            name="gamma",
            dist=pm.Normal.dist(mu=mean_gamma, sigma=sd_gamma),
            lower=0,
            dims="bookmakers",
        )

        # Positionen der tatsaechlich verwendeten Stuetzstellen auf dem
        # Perzentilraster, 1-basiert (OddsMvt0 ist der erste Timestamp) --
        # identisch zu `_gen_meth_mom.momcond`, damit GMM und Bayesian
        # dieselbe Momentbedingung schaetzen.
        tau = [n_per - i * incr + 1 for i in (1, 2, 3)]

        # Zerfallsfaktor = Verhaeltnis der Positionen der beiden jeweils
        # verglichenen Stuetzstellen (Biais et al. 1999, Gl. 12). Bei
        # incr = 1 geht es exakt in ((n_per-1)/n_per) bzw.
        # ((n_per-2)/(n_per-1)) ueber.
        mom_cond_1 = (exog[:, 0] - endog) ** 2 - (
            (tau[1] / tau[0]) ** (2 * gamma[bookie_idx])
        ) * (exog[:, 1] - endog) ** 2
        mom_cond_2 = (exog[:, 1] - endog) ** 2 - (
            (tau[2] / tau[1]) ** (2 * gamma[bookie_idx])
        ) * (exog[:, 2] - endog) ** 2

        # Moment conditions x instruments
        mom_cond = pt.stack([mom_cond_1, mom_cond_2], axis=1)
        mom_conds = (inst[:, :, None] * mom_cond[:, None, :]).reshape(
            (mom_cond.shape[0], 14)
        )

        # Likelihood
        pm.Normal(
            name="moment_conditions",
            mu=mom_conds,
            sigma=sd_eps,
            observed=np.zeros(shape=(df.shape[0], 14)),
            dims=("obs_id", "moment"),
        )

    return model
