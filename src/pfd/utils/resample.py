#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from collections import deque

import pandas as pd

# Function


def resample(
    df: pd.DataFrame, period: int | None, freq: str, pctls
) -> pd.DataFrame:
    """
    Resample time series

    This function resamples a given period of a time-series to a given
    frequency

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    period : int | None
        Sub-period of time-series to be resampled. Use None for total
        series.
    freq : str
        Frequency to which the series is supposed to be resampled
        (e.g. "1min").

    Returns
    -------
    pd.DataFrame
        Resampled DataFrame.
    """
    ix = deque(df.index)

    if df.index.min() > df["TsStart"].iat[0]:
        ix.appendleft(df["TsStart"].iat[0])

    if df.index.max() < df["TsEnd"].iat[0]:
        ix.append(df["TsEnd"].iat[0])

    df = df.reindex(ix).ffill()
    df.loc[:, df.columns != "OddsMvt"] = df.loc[
        :, df.columns != "OddsMvt"
    ].bfill()

    df = df.asfreq(freq=freq, method="ffill")
    df["Update"] = df.index

    if period:
        df = df[(df["Update"].iat[-1] - pd.offsets.Hour(period)) :]

    df["ElapTime"] = df["Update"].diff().fillna(
        pd.Timedelta(seconds=0)
    ).cumsum() / pd.Timedelta(hours=1)

    df = df.loc[
        df["ElapTime"].isin(
            df["ElapTime"].quantile(pctls, interpolation="lower").to_numpy()
        ),
        :,
    ]

    return df
