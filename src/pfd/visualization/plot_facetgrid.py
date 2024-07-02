#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from typing import Dict

import arviz as az
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Function


def plot_facetgrid(
    mod_trace: az.InferenceData | Dict[str, az.InferenceData],
    param: str,
    color_palette: list,
    path: str,
    save: bool,
) -> None:
    """
    Plot kernel densities using seaborn facetgrid.

    Parameters
    ----------
    mod_trace : az.InferenceData | Dict[str, az.InferenceData]
        Record of the sampling process.
    param: str
        Parameter to be plotted.
    color_palette: list
        Color palette.
    path : str
        Path for saving.
    save : bool
        Save figure if True.
    """

    def create_data(data: az.InferenceData) -> pd.DataFrame:
        """
        Create data for facetgrid plot.

        Parameters
        ----------
        data : az.InferenceData
            Trace object.

        Returns
        -------
        pd.DataFrame
            Data for facetgrid plot.
        """
        bookies_vals = data.posterior["bookmakers"].to_numpy()

        param_vals = data.posterior[param].to_numpy()
        param_vals = param_vals.reshape(-1, len(bookies_vals))
        param_vals = pd.DataFrame(data=param_vals, columns=bookies_vals)
        param_vals = pd.melt(
            frame=param_vals,
            value_vars=bookies_vals,
            var_name="Bookies",
            value_name=f"$\\{param}_i$",
        )
        return param_vals

    if isinstance(mod_trace, dict):
        param_vals_pro = create_data(data=mod_trace["Professionals"])
        param_vals_amat = create_data(data=mod_trace["Amateurs"])

        param_vals_pro["Subset"] = "Professionals"
        param_vals_amat["Subset"] = "Amateurs"

        param_vals = pd.concat(
            [param_vals_pro, param_vals_amat], axis=0, ignore_index=True
        )

        g = sns.FacetGrid(
            param_vals,
            col="Bookies",
            col_wrap=6,
            sharex=True,
            sharey=True,
        )
        g.map(
            sns.violinplot,
            f"$\\{param}_i$",
            hue="Subset",
            hue_order=["Professionals", "Amateurs"],
            split=True,
            palette=color_palette[0:2],
            inner="quart",
            gap=0.05,
            data=param_vals,
        )
        g.set_titles(col_template="{col_name}")
        g.set(ylabel="", xlabel="")
        g.add_legend(
            title=None,
            loc="upper center",
            bbox_to_anchor=(0.42, 0.015),
            ncol=2,
        )
        if save:
            plt.savefig(
                fname=path,
                format="pdf",
                transparent=True,
                bbox_inches="tight",
            )
        plt.show(block=False)
    else:
        param_vals = create_data(data=mod_trace)

        g = sns.FacetGrid(
            param_vals,
            col="Bookies",
            col_wrap=6,
            sharex=True,
            sharey=True,
        )
        g.map(
            sns.violinplot,
            f"$\\{param}_i$",
            inner="quart",
            data=param_vals,
        )
        # g.map(sns.kdeplot, f"$\\{param}_i$")
        g.set_titles(col_template="{col_name}")
        g.set(ylabel="", xlabel="")
        if save:
            plt.savefig(
                fname=path,
                format="pdf",
                transparent=True,
                bbox_inches="tight",
            )
        plt.show(block=False)
