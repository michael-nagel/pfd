#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Dict, Tuple

# Imports
import arviz as az
import nutpie
import pymc as pm

# Function


def est_pm_mod(
    model: pm.Model,
    seed: int,
    n_draws: int | None = None,
    n_tune: int | None = None,
    n_chains: int | None = None,
    n_cores: int | None = None,
    targ_acpt: float | None = None,
    vi: bool = False,
    vi_n_iter: int | None = None,
    vi_n_draws: int | None = None,
    *args: tuple,
    **kwargs: Dict[str, Any],
) -> Tuple[Any, Any, Any] | az.InferenceData:
    """
    Estimate PyMC model.

    This function either numerically estimates the defined PyMC model
    using Hamiltonian Monte Carlo methods (NUTS) or approximates the
    results using Variational Inference.

    Parameters
    ----------
    model : pymc.Model
        PyMC model to be numerically estimated.
    seed : int
        Random seed.
    n_draws : int | None, default None
        Number of draws.
    n_tune : int | None, default None
        Number of tuning samples (burn-in).
    n_chains : int | None, default None
        Number of chains.
    n_cores: int | None, default None
        Number of cores.
    targ_acpt : float | None, default None
        Target acceptance rate.
    vi : bool, default False
        Whether variational inference should be used for estimation.
    vi_n_iter: int, default None
        Number of iterations for variational inference.
    vi_n_draws: int, default None
        Number of draws for variational inference.
    *args : tuple
        Parameters specific to the trace.
    **kwargs : Dict[str, Any]
        Parameters specific to the trace.

    Returns
    -------
    Tuple[Any, Any, Any] | arviz.InferenceData
        Record of the estimation process.
    """
    if vi:
        advi = pm.ADVI(model=model, random_seed=seed)

        tracker = pm.callbacks.Tracker(
            mean=advi.approx.mean.eval,  # callable that returns mean
            std=advi.approx.std.eval,  # callable that returns std
        )

        approx = advi.fit(
            n=vi_n_iter,
            obj_optimizer=pm.adagrad_window(learning_rate=0.003),
            callbacks=[
                tracker,
                pm.callbacks.CheckParametersConvergence(diff="absolute"),
            ],
        )

        trace = approx.sample(draws=vi_n_draws)

        return trace, tracker, advi

    else:
        compiled_model = nutpie.compile_pymc_model(model=model)

        trace = nutpie.sample(
            compiled_model=compiled_model,
            draws=n_draws,
            tune=n_tune,
            chains=n_chains,
            cores=n_cores,
            seed=seed,
            target_accept=targ_acpt,
            *args,
            **kwargs,
        )

        return trace
