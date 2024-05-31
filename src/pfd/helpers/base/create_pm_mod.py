#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import numpy as np
import pandas as pd
import pymc as pm

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
    coords = {"bookmakers": bookies, "obs_id": np.arange(0, len(bookie_idx))}

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
            dist=pm.Normal.dist(mu=0, sigma=5),
            lower=0,
        )
        sd_gamma = pm.HalfCauchy(name="sd_gamma", beta=1)
        gamma = pm.Truncated(
            name="gamma",
            dist=pm.Normal.dist(mu=mean_gamma, sigma=sd_gamma),
            lower=0,
            dims="bookmakers",
        )

        # Random effects phi
        mean_phi = pm.Normal(name="mean_Phi", mu=0, sigma=0.1)
        sd_phi = pm.HalfCauchy(name="sd_Phi", beta=0.01)
        phi = pm.Normal(
            name="Phi", mu=mean_phi, sigma=sd_phi, dims="bookmakers"
        )

        # Moment conditions
        mom_cond_1 = (
            (exog[:, 0] - endog) ** 2
            - (((n_per - 1) / n_per) ** (2 * gamma[bookie_idx]))
            * (exog[:, 1] - endog) ** 2
            - phi[bookie_idx]
            * (1 - ((n_per - 1) / n_per) ** (2 * gamma[bookie_idx]))
        )
        mom_cond_2 = (
            (exog[:, 1] - endog) ** 2
            - (((n_per - 2) / (n_per - 1)) ** (2 * gamma[bookie_idx]))
            * (exog[:, 2] - endog) ** 2
            - phi[bookie_idx]
            * (1 - ((n_per - 2) / (n_per - 1)) ** (2 * gamma[bookie_idx]))
        )

        mom_conds = []

        for i in range(0, 7):
            mom_conds.append(mom_cond_1 * inst[:, i])
            mom_conds.append(mom_cond_2 * inst[:, i])

        # Likelihood
        for i, mu in enumerate(mom_conds, start=1):
            pm.Normal(
                name=f"moment_condition_{i}",
                mu=mu,
                sigma=sd_eps,
                observed=np.zeros(shape=df.shape[0]),
                dims="obs_id",
            )

    return model
