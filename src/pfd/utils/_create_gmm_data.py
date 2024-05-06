#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from typing import Tuple

import numpy as np
import pandas as pd


# Function
def _create_gmm_data(
    df: pd.DataFrame, n_per: int, incr: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create GMM data.

    This function creates the GMM data required for estimation.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data.
    n_per : int
        Number of periods to be considered.
    incr : int
        Incremental step for periods.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        GMM data (endog. variables, exog. variables, instruments).

    Raises
    ------
    ValueError
        If 'n_per' is not valid or required columns are missing.
    """
    # Validate inputs
    if not isinstance(n_per, int) or n_per <= 0:
        raise ValueError("Input 'n_per' must be a positive integer.")
    if not isinstance(incr, int) or incr <= 0:
        raise ValueError("Input 'incr' must be a positive integer.")

    # Endogenous variable
    endog = df[f"OddsMvt{n_per - 1}"].to_numpy()

    # Exogenous variables and Instruments
    exog_list = []
    inst_list = [np.ones(shape=endog.shape[0])]

    for i in range(1, 6):
        p = df[f"OddsMvt{n_per - (1 + i * incr)}"].to_numpy()
        exog_list.append(p)

        if i > 3:
            z = exog_list[i - 2] - p
            inst_list.extend([z, z**2])

    exog_list.append(df["OddsMvt0"].to_numpy())

    z = exog_list[4] - exog_list[5]
    inst_list.extend([z, z**2])

    exog, inst = np.column_stack(exog_list), np.column_stack(inst_list)

    # Exogenous variables  # TODO
    # p_t = df[f"OddsMvt{n_per - (1 + 1 * incr)}"].to_numpy()
    # p_t_1 = df[f"OddsMvt{n_per - (1 + 2 * incr)}"].to_numpy()
    # p_t_2 = df[f"OddsMvt{n_per - (1 + 3 * incr)}"].to_numpy()
    # p_t_3 = df[f"OddsMvt{n_per - (1 + 4 * incr)}"].to_numpy()
    # p_t_4 = df[f"OddsMvt{n_per - (1 + 5 * incr)}"].to_numpy()
    # p_0 = df["OddsMvt0"].to_numpy()
    # exog = np.column_stack((p_t, p_t_1, p_t_2, p_t_3, p_t_4, p_0))

    # # Instruments
    # z_1 = np.ones(shape=endog.shape[0])
    # z_2 = p_t_2 - p_t_3
    # z_3 = (p_t_2 - p_t_3) ** 2
    # z_4 = p_t_3 - p_t_4
    # z_5 = (p_t_3 - p_t_4) ** 2
    # z_6 = p_t_4 - p_0
    # z_7 = (p_t_4 - p_0) ** 2
    # inst = np.column_stack((z_1, z_2, z_3, z_4, z_5, z_6, z_7))
    return endog, exog, inst
