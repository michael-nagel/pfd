#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

import numpy as np
from statsmodels.sandbox.regression.gmm import GMM
from typing import List

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

    def momcond(self, params: np.ndarray) -> np.ndarray:
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
        param_0, param_1 = params
        n_per = self.n_per
        endog = self.endog
        exog = self.exog
        inst = self.instrument

        # Moment conditions
        mom_cond_1 = (
            (exog[:, 0] - endog) ** 2
            - (((n_per - 1) / n_per) ** (2 * param_0))
            * (exog[:, 1] - endog) ** 2
            - param_1 * (1 - ((n_per - 1) / n_per) ** (2 * param_0))
        )
        mom_cond_2 = (
            (exog[:, 1] - endog) ** 2
            - (((n_per - 2) / (n_per - 1)) ** (2 * param_0))
            * (exog[:, 2] - endog) ** 2
            - param_1 * (1 - ((n_per - 2) / (n_per - 1)) ** (2 * param_0))
        )

        # Additional moment conditions created by instruments
        list_mom_conds: List[np.ndarray] = []
        for i in range(0, 7):
            list_mom_conds.append(mom_cond_1 * inst[:, i])
            list_mom_conds.append(mom_cond_2 * inst[:, i])

        mom_conds = np.column_stack(list_mom_conds)

        # m_1 = mom_cond_1 * inst[:, 0]  # TODO
        # m_2 = mom_cond_2 * inst[:, 0]
        # m_3 = mom_cond_1 * inst[:, 1]
        # m_4 = mom_cond_2 * inst[:, 1]
        # m_5 = mom_cond_1 * inst[:, 2]
        # m_6 = mom_cond_2 * inst[:, 2]
        # m_7 = mom_cond_1 * inst[:, 3]
        # m_8 = mom_cond_2 * inst[:, 3]
        # m_9 = mom_cond_1 * inst[:, 4]
        # m_10 = mom_cond_2 * inst[:, 4]
        # m_11 = mom_cond_1 * inst[:, 5]
        # m_12 = mom_cond_2 * inst[:, 5]
        # m_13 = mom_cond_1 * inst[:, 6]
        # m_14 = mom_cond_2 * inst[:, 6]

        # m = np.column_stack(
        #     (
        #         m_1,
        #         m_2,
        #         m_3,
        #         m_4,
        #         m_5,
        #         m_6,
        #         m_7,
        #         m_8,
        #         m_9,
        #         m_10,
        #         m_11,
        #         m_12,
        #         m_13,
        #         m_14,
        #     )
        # )

        return mom_conds
