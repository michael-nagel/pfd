#!/usr/bin/env python3

"""
This file filters and shapes the estimation sample.
"""

# Imports

import numpy as np
import pandas as pd

from pfd.utils import PFDConfig, enc_categ_var, scale_vars

# Function


def filter_and_shape_data(
    df: pd.DataFrame, cfg: PFDConfig
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    list[str],
    list[str],
    int,
    int,
    float,
    float,
]:
    """
    Filter and shape the estimation sample.

    This function applies the margin/bookmaker/time-series-duration
    filters, determines favorites/longshots, takes the home or away
    perspective, and encodes the exogenous variables used throughout
    the rest of the estimation.

    Parameters
    ----------
    df : pd.DataFrame
        Shaped data as produced by shape_data().
    cfg : PFDConfig
        Config parameters.

    Returns
    -------
    tuple
        df, df_desc, bookies, exog_cols, n_obs, n_groups, is_amateur,
        is_pro.
    """
    # Store number of observations before filtering
    n_obs = df.shape[0]

    # Filter competitions
    if cfg.estimation.compets:
        df = df.loc[df["Competition"].isin(cfg.estimation.compets)]

    # Calculate margin and remove observations with inplausible margins
    df["Margin"] = 1 / df["OddsMvtHome"] + 1 / df["OddsMvtAway"] - 1
    df = df.loc[(df["Margin"] >= 0) & (df["Margin"] <= 0.15)]

    # Create unique group IDs
    df["GroupId"] = df.groupby(["Matchup", "Bookies"]).ngroup()

    # Calculate number of groups
    n_groups = df["GroupId"].nunique()

    # Discard small bookmakers contributing few obs. to the sample
    df = df[
        df.groupby("Bookies")["Bookies"].transform("size")
        > df["Bookies"].value_counts().quantile(cfg.estimation.bm_quantile)
    ]

    # Determine favorite and longshot
    condition = (
        df.groupby("GroupId")["OddsMvtHome"].first()
        < df.groupby("GroupId")["OddsMvtAway"].first()
    ) | (
        (
            df.groupby("GroupId")["OddsMvtHome"].first()
            == df.groupby("GroupId")["OddsMvtAway"].first()
        )
        & (
            df.groupby("GroupId")["OddsMvtHome"].last()
            < df.groupby("GroupId")["OddsMvtAway"].last()
        )
    )

    df["IsFav"] = df["GroupId"].map(condition).astype(int)

    # Take home/away perspective
    if cfg.estimation.spec == "BmHome":
        df = df.drop("OddsMvtAway", axis=1)
        df = df.rename(columns={"OddsMvtHome": "OddsMvt"})
        df["Match"] = df["Match"] + 1
        df.loc[df["Match"] == 2, "Match"] = 0
    else:
        df = df.drop("OddsMvtHome", axis=1)
        df = df.rename(columns={"OddsMvtAway": "OddsMvt"})

    # Calculate the time series duration from open to close
    df["TsDur"] = (
        df.groupby("GroupId")["Update"].transform("last")
        - df.groupby("GroupId")["Update"].transform("first")
    ) / np.timedelta64(1, "h")

    # Keep time series with specific time series lengths
    df = df[
        (df["TsDur"] >= cfg.estimation.ts_dur[0])
        & (df["TsDur"] <= cfg.estimation.ts_dur[1])
    ]

    # Calculate number of odds movements
    df["NumOddsMvt"] = df.groupby("GroupId")["GroupId"].transform("size")
    df["NumOddsMvt"] = df["NumOddsMvt"] - 1

    # Calculate implied probabilities
    df["OddsMvt"] = 1 / df["OddsMvt"]

    # Determine opening and closing odds
    df = df.assign(
        OpnOdds=df.groupby("GroupId")["OddsMvt"].transform("first"),
        ClsOdds=df.groupby("GroupId")["OddsMvt"].transform("last"),
    )

    # Create list of bookmakers
    bookies = sorted(list(df["Bookies"].unique()))

    # Assign competitions to pro and amateur and calculate their share
    df["IsPro"] = 0
    df.loc[df["Competition"].isin(["ATP", "WTA"]), "IsPro"] = 1

    is_amateur, is_pro = df["IsPro"].value_counts(True).tolist()

    # Store DataFrame for creating descriptive statistics
    df_desc = df.copy()

    # Filter columns
    df = df[
        [
            "Matchup",
            "GroupId",
            "Competition",
            "IsPro",
            "IsFav",
            "Bookies",
            "NumOddsMvt",
            "TsDur",
            "Match",
            "Update",
            "OddsMvt",
            "OpnOdds",
            "ClsOdds",
        ]
    ]

    # Encode categorical variables
    df = enc_categ_var(
        df=df,
        col="Competition",
        prefix="Compet",
        rm_first=True,
        rm_categ_var=True,
    )

    # Standardization
    df["TsDur"] = scale_vars(df["TsDur"].to_numpy().reshape(-1, 1))

    # Create list of exogenous variables
    exog_cols = [col for col in df.columns if col.startswith("Compet")] + [
        "TsDur"
    ]

    return df, df_desc, bookies, exog_cols, n_obs, n_groups, is_amateur, is_pro
