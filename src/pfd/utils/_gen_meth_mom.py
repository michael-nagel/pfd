#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from typing import List

import numpy as np
from statsmodels.sandbox.regression.gmm import GMM

# Class


class _GenMethMom(GMM):

    def __init__(
        self,
        endog,
        exog,
        instrument,
        k_moms=None,
        k_params=None,
        missing="none",
        **kwds
    ):
        super().__init__(
            endog, exog, instrument, k_moms, k_params, missing, **kwds
        )

    def momcond(self, param: np.ndarray) -> np.ndarray:
        """
        Create the moment conditions for GMM.

        This function generates the moment conditions for GMM estimation.

        Parameters
        ----------
        params : np.ndarray
            Starting parameters.

        Returns
        -------
        np.ndarray
            Moment conditions.
        """
        n_per = self.n_per
        endog = self.endog
        exog = self.exog
        inst = self.instrument

        # Moment conditions
        mom_cond_1 = (exog[:, 0] - endog) ** 2 - (
            ((n_per - 1) / n_per) ** (2 * param)
        ) * (exog[:, 1] - endog) ** 2
        mom_cond_2 = (exog[:, 1] - endog) ** 2 - (
            ((n_per - 2) / (n_per - 1)) ** (2 * param)
        ) * (exog[:, 2] - endog) ** 2

        # Additional moment conditions created by instruments
        list_mom_conds: List[np.ndarray] = []
        for i in range(0, 7):
            list_mom_conds.append(mom_cond_1 * inst[:, i])
            list_mom_conds.append(mom_cond_2 * inst[:, i])

        mom_conds = np.column_stack(list_mom_conds)

        return mom_conds
