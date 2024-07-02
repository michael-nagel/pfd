#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss

# Function


def calc_losses(grouped_df: pd.DataFrame) -> list:
    """
    Calculate the Brier score loss and the log loss of each group.

    Parameters
    ----------
    df : pd.DataFrame
        Grouped DataFrame.

    Returns
    -------
    list
        List containing the brier score loss and the log loss.

    """
    b_loss = brier_score_loss(
        y_true=grouped_df["Match"], y_prob=grouped_df["OpnOdds"]
    )
    l_loss = log_loss(y_true=grouped_df["Match"], y_pred=grouped_df["OpnOdds"])
    return [b_loss, l_loss]
