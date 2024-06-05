#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import matplotlib.pyplot as plt

# Function


def finalize_plot(path: str, save: bool, fmt: str = "pdf") -> None:
    """
    Finalize plot.

    This function finalizes a plot .

    Parameters
    ----------
    path : str
        The location and file name for the plot to be stored.
    save : bool
        Save figure if True.
    """
    plt.tight_layout()
    if save:
        plt.savefig(
            fname=path,
            format=fmt,
            dpi=600,
            transparent=True,
            bbox_inches="tight",
        )
    plt.show(block=False)
