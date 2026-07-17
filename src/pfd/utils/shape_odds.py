#!/usr/bin/env python3

# Imports

import numpy as np
import pandas as pd

# Function


def shape_odds(df: pd.DataFrame, cols_base: list, side: str) -> pd.DataFrame:
    """
    Shape the crawled odds.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    cols_base : list
        List containing the base columns.
    side : str
        Side (Home or Away).

    Returns
    -------
    pd.DataFrame
        Shaped data.
    """

    df = df[cols_base + ["Bookies", "Payout", f"Odds{side}"]]

    df = df.loc[df[f"Odds{side}"].notna()]
    df = df.reset_index(drop=True)

    bookies_lengths = df["Bookies"].map(len)
    payout_lengths = df["Payout"].map(len)
    odds_lengths = df[f"Odds{side}"].map(len)

    df = df[
        (bookies_lengths == payout_lengths) & (bookies_lengths == odds_lengths)
    ]

    df = df.reset_index(drop=True)

    df = df.explode(["Bookies", "Payout", f"Odds{side}"])
    df = df.reset_index(drop=True)

    df = df.loc[df["Payout"] != "-", :]
    df = df.loc[df[f"Odds{side}"].notna()]
    df = df.loc[df[f"Odds{side}"].str.startswith("ODDS MOVEMENT")]
    df = df.reset_index(drop=True)

    df = df.drop_duplicates(keep="first")
    df = df.drop_duplicates(
        subset=[col for col in df if col not in ["Payout", f"Odds{side}"]],
        keep="first",
    )
    df = df.reset_index(drop=True)

    df[f"Odds{side}"] = df[f"Odds{side}"].str.replace(
        "ODDS MOVEMENT\n", "", regex=True
    )
    df["OddsMvt"] = df[f"Odds{side}"].str.split(pat="Opening odds:\n").str[0]
    df["OpnOdds"] = df[f"Odds{side}"].str.split(pat="Opening odds:\n").str[-1]

    df["OddsMvt"] = df["OddsMvt"].str.replace(
        pat=r"(\-|\+)\d.\d\d\n", repl="", regex=True
    )

    df["Update"] = (
        df["OddsMvt"].str.split(pat=r"(\d\d [^']{3}, \d\d:\d\d)\n").str[:-1]
    )
    df["Update"] = df["Update"].map(lambda x: [ele for ele in x if ele != ""])

    df["OddsMvt"] = (
        df["OddsMvt"].str.split(pat=r"(\d\d [^']{3}, \d\d:\d\d)\n").str[-1]
    )
    df["OddsMvt"] = df["OddsMvt"].str.split(pat="\n")
    df["OddsMvt"] = df["OddsMvt"].map(lambda x: [ele for ele in x if ele != ""])

    df[["DtOpnOdds", "OpnOdds"]] = df["OpnOdds"].str.split(
        pat="\n", n=1, expand=True, regex=False
    )

    df = df.dropna()
    df = df.reset_index(drop=True)

    for i in range(0, len(df)):
        df.at[i, "OddsMvt"].append(df.at[i, "OpnOdds"])
        df.at[i, "Update"].append(df.at[i, "DtOpnOdds"])

    df = df.drop([f"Odds{side}", "OpnOdds", "DtOpnOdds"], axis=1)
    df = df.loc[
        df["OddsMvt"].map(lambda x: len(x))
        == df["Update"].map(lambda x: len(x)),
        :,
    ]

    df = df.explode(["Update", "OddsMvt"])

    # Oddsportal usually provides opening odds + the last 20 odds movements.
    # For plausability reasons, don't keep cases with more than 21 observations
    group_sizes = df.groupby(["Matchup", "Bookies"])["Matchup"].transform(len)
    df = df[group_sizes <= 21]
    df = df.reset_index(drop=True)

    df = df.loc[df["Date"] >= "2023-01-01 00:00:00"]
    df = df.reset_index(drop=True)

    df["OddsMvt"] = pd.to_numeric(arg=df["OddsMvt"], errors="coerce")
    df["Update"] = df["Date"].dt.year.astype(str) + " " + df["Update"]
    df["Update"] = pd.to_datetime(
        arg=df["Update"], errors="coerce", yearfirst=True
    )

    df = df.dropna()
    df = df.reset_index(drop=True)

    df["Payout"] = df["Payout"].str.replace("%", "")
    df["Payout"] = df["Payout"].astype(float)

    conditions = [
        df["Tournament"].str.contains("ATP", case=False),
        df["Tournament"].str.contains("WTA", case=False),
        df["Tournament"].str.contains("ITF", case=False)
        & df["Tournament"].str.contains("Men", case=False),
        df["Tournament"].str.contains("ITF", case=False)
        & df["Tournament"].str.contains("Women", case=False),
        df["Tournament"].str.contains("Challenger", case=False)
        & df["Tournament"].str.contains("Men", case=False),
        df["Tournament"].str.contains("Challenger", case=False)
        & df["Tournament"].str.contains("Women", case=False),
    ]

    choices = [
        "ATP",
        "WTA",
        "ITF Men",
        "ITF Women",
        "Challenger Men",
        "Challenger Women",
    ]

    df["Competition"] = np.select(conditions, choices, default="Misc")

    df["Matchup"] = df.groupby(
        ["Date", "Encounter", "Country", "Tournament"]
    ).ngroup()

    df = df.sort_values(
        by=["Date", "Encounter", "Country", "Tournament", "Bookies", "Update"]
    )

    # Drop duplicates
    df = df.drop_duplicates()

    # If there are multiple updates with the same timestamp, keep last
    df = df.drop_duplicates(
        subset=list(df.columns.difference(["OddsMvt"])), keep="last"
    )

    df = df.reset_index(drop=True)

    for col in [
        "Encounter",
        "Country",
        "Tournament",
        "Bookies",
        "Competition",
    ]:
        df[col] = df[col].astype(str)

    return df
