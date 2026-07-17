#!/usr/bin/env python3

# Imports

import arviz as az
import matplotlib.pyplot as plt
import seaborn as sns

from pfd.utils import finalize_plot

# Function


# def plot_traces(
#     mod_trace: az.InferenceData, param: str, path: str, save: bool
# ) -> None:
#     """
#     Plot posterior distributions.

#     Parameters
#     ----------
#     mod_trace : az.InferenceData
#         Record of the sampling process.
#     param: str
#         Parameter to be plotted.
#     path : str
#         Path for saving.
#     save : bool
#         Save figure if True.
#     """
#     bookies_traces = mod_trace.posterior["bookmakers"].to_numpy()
#     param_vals = mod_trace.posterior[param].to_numpy()

#     _, ax = plt.subplots(
#         nrows=len(bookies_traces), ncols=2, figsize=(6.4, 28.8)
#     )
#     for i, bookie in enumerate(bookies_traces):
#         for c in range(0, param_vals.shape[0]):
#             sns.kdeplot(
#                 param_vals[c, :, i].flatten(), label=bookie, ax=ax[i, 0]
#             )
#             ax[i, 1].plot(param_vals[c, :, i].flatten(), label=bookie)
#         ax[i, 0].set(xlabel="", ylabel="", title=bookie)
#         ax[i, 1].set(xlabel="", ylabel="", title=bookie)
#         if param == "Phi":
#             ax[i, 0].ticklabel_format(
#                 style="sci", scilimits=(0, 0), axis="both"
#             )
#             ax[i, 1].ticklabel_format(style="sci", scilimits=(0, 0),
#                                       axis="y")
#     finalize_plot(path=path, save=save)


def plot_traces(
    mod_trace: az.InferenceData, param: str, path: str, save: bool
) -> None:
    """
    Plot posterior distributions.

    Parameters
    ----------
    mod_trace : az.InferenceData
        Record of the sampling process.
    param: str
        Parameter to be plotted.
    path : str
        Path for saving.
    save : bool
        Save figure if True.
    """
    bookies_traces = mod_trace.posterior["bookmakers"].to_numpy()
    param_vals = mod_trace.posterior[param].to_numpy()

    n_bookies = len(bookies_traces)
    mid_point = n_bookies // 2

    # First half
    fig1, ax1 = plt.subplots(nrows=mid_point, ncols=2, figsize=(6.4, 12))
    for i, bookie in enumerate(bookies_traces[:mid_point]):
        for c in range(0, param_vals.shape[0]):
            sns.kdeplot(
                param_vals[c, :, i].flatten(), label=bookie, ax=ax1[i, 0]
            )
            ax1[i, 1].plot(param_vals[c, :, i].flatten(), label=bookie)
        ax1[i, 0].set(xlabel="", ylabel="", title=bookie)
        ax1[i, 1].set(xlabel="", ylabel="", title=bookie)
        ax1[i, 0].title.set_size(10)
        ax1[i, 1].title.set_size(10)
    finalize_plot(path=path[0], save=save)

    # Second half
    fig2, ax2 = plt.subplots(
        nrows=n_bookies - mid_point, ncols=2, figsize=(6.4, 12)
    )
    for i, bookie in enumerate(bookies_traces[mid_point:]):
        for c in range(0, param_vals.shape[0]):
            sns.kdeplot(
                param_vals[c, :, i + mid_point].flatten(),
                label=bookie,
                ax=ax2[i, 0],
            )
            ax2[i, 1].plot(
                param_vals[c, :, i + mid_point].flatten(), label=bookie
            )
        ax2[i, 0].set(xlabel="", ylabel="", title=bookie)
        ax2[i, 1].set(xlabel="", ylabel="", title=bookie)
        ax2[i, 0].title.set_size(10)
        ax2[i, 1].title.set_size(10)
    finalize_plot(path=path[1], save=save)
