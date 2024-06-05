#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file shapes the crawled data.
"""

# Imports

import json
from typing import Any, List

import hydra
import pandas as pd
from hydra.core.config_store import ConfigStore

from pfd.helpers import save_values
from pfd.utils import Logger, PFDConfig, shape_odds

# Hydra Setup

cs = ConfigStore.instance()
cs.store(name="pfd_config", node=PFDConfig)

# Function


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def shape_data(cfg: PFDConfig) -> None:
    # Logging

    log = Logger.init_logger(name=__name__)
    t_start = Logger.get_time()

    # External Files

    data: List[Any] = []
    for line in open(f"{cfg.paths.data_raw}crawled_odds.json", "r"):
        try:
            data.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    # Shaping

    df = pd.DataFrame(data)

    n_matches_tot = df.shape[0]
    n_bm_tot = df["Bookies"].map(len).max()
    timestamps = df["Timestamp"].copy()

    df = df.dropna(
        subset=[
            "Encounter",
            "Timestamp",
            "Date",
            "Country",
            "Tournament",
            "Result",
        ],
        how="any",
    )
    df = df.reset_index(drop=True)

    df = df.loc[df["Result"].str.startswith("Final result"), :]

    df["Date"] = df["Date"].str.replace(
        pat=r"(To|Yester|Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day, ",
        repl="",
        regex=True,
    )
    df["Date"] = df["Date"].str.strip()

    df = df.loc[
        df["Date"].str.contains(
            pat=r"^\d{2} [a-zA-Z]{3} \d{4}, \d{2}:\d{2}$", regex=True
        )
    ]
    df = df.reset_index(drop=True)

    df["Date"] = pd.to_datetime(arg=df["Date"])

    df["Tournament"] = df["Tournament"].str.replace(
        r"\d{4}\s*$", "", regex=True
    )
    df["Tournament"] = df["Tournament"].str.rstrip()

    df["Score"] = df["Result"].str.split(pat="\n").str[1]

    df["Match"] = 0
    df.loc[df["Score"].isin(["0:2", "1:2", "0:3", "1:3", "2:3"]), "Match"] = 1

    df["Matchup"] = df.groupby(
        ["Date", "Encounter", "Country", "Tournament"]
    ).ngroup()
    df = df.sort_values(by="Matchup")
    df = df.reset_index(drop=True)

    cols_base = [
        "Matchup",
        "Date",
        "Encounter",
        "Country",
        "Tournament",
        "Match",
    ]

    #

    # def shape_prices(df, price):
    #     # TODO check if the volume is the same if there is the same price for
    #     # two subsequent rows
    #     # df_original = df.copy()
    #     # price = "PriceBackHome"

    #     df = df[cols_base + ["Exng", "PayoutExng", price]].copy()

    #     df = df.loc[df[price].notna()]
    #     df = df.reset_index(drop=True)

    #     if "Back" in price:
    #         df["PayoutExng"] = df["PayoutExng"].apply(lambda x: x[0::2])
    #     else:
    #         df["PayoutExng"] = df["PayoutExng"].apply(lambda x: x[1::2])

    #     df = df.loc[
    #         (
    #             df["Exng"].apply(lambda x: len(x))
    #             == df["PayoutExng"].apply(lambda x: len(x))
    #         )
    #         & (
    #             df["Exng"].apply(lambda x: len(x))
    #             == (df[price].apply(lambda x: len(x)))
    #         )
    #         & (
    #             df["PayoutExng"].apply(lambda x: len(x))
    #             == (df[price].apply(lambda x: len(x)))
    #         )
    #     ]
    #     df = df.reset_index(drop=True)

    #     df = df.explode(["Exng", "PayoutExng", price])
    #     df = df.reset_index(drop=True)

    #     df = df.loc[df["PayoutExng"] != "-", :]
    #     df = df.reset_index(drop=True)

    #     df = df.loc[(df[price].apply(lambda x: len(x)) == 1)]
    #     df[price] = df[price].apply(lambda x: x[0])

    #     df[price] = df[price].str.replace("ODDS MOVEMENT\n", "", regex=True)

    #     df["OddsMvt"] = df[price].str.split(pat="Opening odds:\n").str[0]
    #     df["OpnOdds"] = df[price].str.split(pat="Opening odds:\n").str[-1]

    #     df["OddsMvt"] = df["OddsMvt"].str.replace(
    #         pat=r"(\-|\+)\d.\d\d\n", repl="", regex=True
    #     )

    #     df["Update"] = (
    #         df["OddsMvt"]
    #         .str.split(pat=r"(\d\d [^']{3}, \d\d:\d\d)\n")
    #         .str[:-1]
    #     )
    #     df["Update"] = df["Update"].apply(
    #         lambda x: [ele for ele in x if ele != ""]
    #     )

    # df["OddsMvt"] = (
    #     df["OddsMvt"].str.split(
    #         pat=r"(\d\d [^']{3}, \d\d:\d\d)\n").str[-1]
    # )
    #     df = df.loc[(df["OddsMvt"].apply(lambda x: len(x)) > 0)]

    #     df[["OddsMvt", "Volume"]] = df["OddsMvt"].str.split(
    #         pat="(", n=1, expand=True
    #     )
    #     df["OddsMvt"] = df["OddsMvt"].str.split(pat="\n")
    #     df["OddsMvt"] = df["OddsMvt"].apply(
    #         lambda x: [ele for ele in x if ele != ""]
    #     )

    # df["Volume"] = df["Volume"].str.replace(
    #     pat="(", repl="", regex=False
    #     )
    # df["Volume"] = df["Volume"].str.replace(
    #     pat=")", repl="", regex=False
    #     )
    #     df["Volume"] = df["Volume"].str.split(pat="\n")
    #     df = df.dropna()
    #     df["Volume"] = df["Volume"].apply(
    #         lambda x: [ele for ele in x if ele != ""]
    #     )

    #     df[["DtOpnOdds", "OpnOdds", "VolumeOpn"]] = df["OpnOdds"].str.split(
    #         pat="\n", n=2, expand=True, regex=False
    #     )

    #     df["VolumeOpn"] = df["VolumeOpn"].str.replace(
    #         pat="(", repl="", regex=False
    #     )
    #     df["VolumeOpn"] = df["VolumeOpn"].str.replace(
    #         pat=")", repl="", regex=False
    #     )

    #     df = df.dropna()
    #     df = df.reset_index(drop=True)

    #     for i in range(0, len(df)):
    #         df.at[i, "OddsMvt"].append(df.at[i, "OpnOdds"])
    #         df.at[i, "Update"].append(df.at[i, "DtOpnOdds"])
    #         df.at[i, "Volume"].append(df.at[i, "VolumeOpn"])

    #     df = df.drop([price, "OpnOdds", "DtOpnOdds", "VolumeOpn"], axis=1)

    #     df = df.loc[
    #         (
    #             df["OddsMvt"].apply(lambda x: len(x))
    #             == df["Update"].apply(lambda x: len(x))
    #         )
    #         & (
    #             df["OddsMvt"].apply(lambda x: len(x))
    #             == df["Volume"].apply(lambda x: len(x))
    #         )
    #         & (
    #             df["Update"].apply(lambda x: len(x))
    #             == df["Volume"].apply(lambda x: len(x))
    #         ),
    #         :,
    #     ]

    #     df = df.explode(["Update", "OddsMvt", "Volume"])
    #     df = df.reset_index(drop=True)

    #     df[["OddsMvt", "Volume"]] = df[["OddsMvt", "Volume"]].apply(
    #         pd.to_numeric, errors="coerce"
    #     )
    #     df["Update"] = df["Date"].dt.year.astype(str) + " " + df["Update"]
    #     df["Update"] = pd.to_datetime(
    #         arg=df["Update"], errors="coerce", yearfirst=True
    #     )

    #     df = df.dropna()
    #     df = df.reset_index(drop=True)

    #     df["Competition"] = None
    #     df.loc[
    #         df["Tournament"].str.contains("ATP", case=False), "Competition"
    #     ] = "ATP"
    #     df.loc[
    #         df["Tournament"].str.contains("WTA", case=False), "Competition"
    #     ] = "WTA"
    #     df.loc[
    #         df["Tournament"].str.contains("ITF", case=False)
    #         & df["Tournament"].str.contains("Men", case=False),
    #         "Competition",
    #     ] = "ITF Men"
    #     df.loc[
    #         df["Tournament"].str.contains("ITF", case=False)
    #         & df["Tournament"].str.contains("Women", case=False),
    #         "Competition",
    #     ] = "ITF Women"
    #     df.loc[
    #         df["Tournament"].str.contains("Challenger", case=False)
    #         & df["Tournament"].str.contains("Men", case=False),
    #         "Competition",
    #     ] = "Challenger Men"
    #     df.loc[
    #         df["Tournament"].str.contains("Challenger", case=False)
    #         & df["Tournament"].str.contains("Women", case=False),
    #         "Competition",
    #     ] = "Challenger Women"

    #     df["Matchup"] = df.groupby(
    #         ["Date", "Encounter", "Country", "Tournament"]
    #     ).ngroup()

    # df = df.sort_values(
    #     by=["Date", "Encounter", "Country", "Tournament", "Exng",
    #         "Update"]
    # )

    #     return df

    df_bm_home = shape_odds(df=df, cols_base=cols_base, side="Home")
    df_bm_away = shape_odds(df=df, cols_base=cols_base, side="Away")

    # Call the function shape_prices
    # df_exng_back_home = shape_prices(df=df, price="PriceBackHome")
    # df_exng_back_away = shape_prices(df=df, price="PriceBackAway")
    # df_exng_lay_home = shape_prices(df=df, price="PriceLayHome")
    # df_exng_lay_away = shape_prices(df=df, price="PriceLayAway")

    # Saving

    if cfg.general.save:
        values_path = f"{cfg.paths.vals}{cfg.files.vals}"
        save_values(
            key="n_matches_tot", value=n_matches_tot, file_name=values_path
        )
        save_values(key="n_bm_tot", value=n_bm_tot, file_name=values_path)

        timestamps.to_hdf(
            path_or_buf=f"{cfg.paths.data_proc}timestamps.h5",
            key="timestamps",
            mode="w",
        )

        for i, (key, val) in enumerate(
            {"BmHome": df_bm_home, "BmAway": df_bm_away}.items()
        ):
            mode = "a" if i > 0 else "w"
            val.to_hdf(
                path_or_buf=f"{cfg.paths.data_proc}shaped_data.h5",
                key=f"{key}",
                mode=mode,
            )

    # Execution Time and Log File Finish

    log.info(f"Execution time: {Logger.get_exec_time(start_time=t_start)}")


if __name__ == "__main__":
    shape_data()
