#!/usr/bin/env python3

"""
Checkpointing for long estimation runs.

The switch `cfg.estimation.checkpoint` controls only whether results are
written to and read from disk. It never changes what is computed: with the
switch off the wrapped callable is invoked and its result returned directly,
with the switch on and no checkpoint present the same callable is invoked and
its result additionally written out.

Pickle is used deliberately: the checkpointed objects are pandas DataFrames,
arviz InferenceData and nested result dicts, which JSON cannot represent. The
files are written and read by this pipeline only, into the project's own
`data/interim/`, and are never transported or accepted from elsewhere - they
are our own intermediate state, not untrusted input.
"""

# Imports

import logging
import os
import pickle
from collections.abc import Callable
from typing import Any

# Function


def run_phase(name: str, fn: Callable[[], Any], cfg: Any) -> Any:
    """
    Run a phase, or load its result from a previous run.

    Parameters
    ----------
    name : str
        Phase name, used as the file name of the checkpoint.
    fn : Callable
        Zero-argument callable producing the phase result.
    cfg : PFDConfig
        Config parameters.

    Returns
    -------
    Any
        Whatever `fn` returns.
    """
    log = logging.getLogger(__name__)

    if not getattr(cfg.estimation, "checkpoint", False):
        return fn()

    path = f"{cfg.paths.data_intrm}ckpt_{name}.pkl"

    if os.path.isfile(path):
        log.info(f"Checkpoint {name}: loading {path}")
        with open(path, "rb") as f:
            return pickle.load(f)

    log.info(f"Checkpoint {name}: computing")
    res = fn()

    tmp = f"{path}.tmp"
    with open(tmp, "wb") as f:
        pickle.dump(res, f)
    os.replace(tmp, path)
    log.info(f"Checkpoint {name}: written to {path}")

    return res
