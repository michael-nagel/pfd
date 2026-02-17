#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Function


def scale_vars(
    X: pd.DataFrame | np.ndarray, with_mean: bool = True, with_std: bool = True
) -> np.ndarray:
    """
    Standardize variables.

    This function standardizes features by removing the mean and scaling
    to unit variance.

    Parameters
    ----------
    df : pd.DataFrame | np.ndarray
        Data to be standardized.
    with_mean : bool, default True
         If True, scale the data to zero mean.
    with_std : bool, default True
        If True, scale the data to unit variance (or equivalently, unit
        standard deviation).

    Returns
    -------
    np.ndarray
        Standardized data.
    """
    scaler = StandardScaler(with_mean=with_mean, with_std=with_std)

    return scaler.fit_transform(X)
