# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import pandas as pd
from omegaconf import DictConfig

# Function


def format_sum(df: pd.DataFrame, cfg: DictConfig) -> pd.DataFrame:
    """
    Format summary DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Summary DataFrame obtained from PyMC sampling.
    cfg : DictConfig
        Dictionary containing the config parameters.

    Returns
    -------
    pd.DataFrame
        Formatted DataFrame.
    """
    hdi_lwr = round(((1 - cfg.sampling.hdi) / 2) * 100, 2)
    hdi_upr = round((1 - (1 - cfg.sampling.hdi) / 2) * 100, 2)
    cols_nuts = [
        "mean",
        "sd",
        "median",
        "std_median",
        f"hdi_{hdi_lwr}%",
        f"hdi_{hdi_upr}%",
        "r_hat",
    ]

    df = df[cols_nuts]
    df = df.rename(
        columns={
            "sd": "std_mean",
            f"hdi_{hdi_lwr}%": f"$hdi^{{{hdi_lwr}}}\\%$",
            f"hdi_{hdi_upr}%": f"$hdi^{{{hdi_upr}}}\\%$",
            "r_hat": "$\\hat{R}$",
        }
    )

    rows_nuts = (
        ["mean_gamma", "sd_gamma"]
        + [row for row in df.index if row.startswith("gamma[")]
        + ["mean_Phi", "sd_Phi"]
        + [row for row in df.index if row.startswith("Phi[")]
        + ["sd_eps"]
    )
    df = df.loc[rows_nuts, :]

    df = df.rename(
        index={
            "mean_gamma": "$\\hat{\\mu}_{\\gamma}$",
            "mean_Phi": "$\\hat{\\mu}_{\\Phi}$",
            "sd_gamma": "$\\hat{\\sigma}_{\\gamma}$",
            "sd_Phi": "$\\hat{\\sigma}_{\\Phi}$",
            "sd_eps": "$\\hat{\\sigma}$",
        }
    )

    new_index = {
        idx: idx.replace("gamma[", "$\\hat{\\gamma}_{")
        .replace("Phi[", "$\\hat{\\Phi}_{")
        .replace("]", "}$")
        for idx in df.index
    }
    df = df.rename(index=new_index)
    return df
