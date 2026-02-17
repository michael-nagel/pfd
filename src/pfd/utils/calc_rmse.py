#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import numpy as np
import pandas as pd

# Function


def calc_rmse(y_true: pd.DataFrame, y_pred: pd.DataFrame) -> list:
    """
    Calculate the root mean squared error of each group.

    Parameters
    ----------
    y_true : pd.DataFrame
        Grouped DataFrame containing true values.
    y_pred : pd.DataFrame
        Grouped DataFrame containing predicted values.

    Returns
    -------
    np.ndarray
        Root mean squared error.

    """
    return np.sqrt(np.mean((y_true - y_pred) ** 2))
