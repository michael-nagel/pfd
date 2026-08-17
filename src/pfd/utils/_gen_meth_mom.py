#!/usr/bin/env python3

# Imports


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
        **kwds,
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
        incr = self.incr
        endog = self.endog
        exog = self.exog
        inst = self.instrument

        # Positionen der tatsaechlich verwendeten Stuetzstellen auf dem
        # Perzentilraster. `_create_gmm_data` zieht
        # OddsMvt{n_per - 1 - (i-1)*incr} fuer i = 1..5; gezaehlt wird
        # 1-basiert, OddsMvt0 ist der erste Timestamp, also tau = Index + 1.
        # MUSS mit der Spaltenwahl dort zusammen geaendert werden.
        tau = [n_per - (i - 1) * incr for i in (1, 2, 3)]

        # Zerfallsfaktor = Verhaeltnis der Positionen der beiden jeweils
        # verglichenen Stuetzstellen (Biais et al. 1999, Gl. 12: ((t-1)/t)).
        # Das Verhaeltnis ist einheitsfrei; entscheidend ist, dass es zum
        # tatsaechlichen Abstand der Stuetzstellen passt. Bei incr = 1 geht
        # es exakt in ((n_per-1)/n_per) bzw. ((n_per-2)/(n_per-1)) ueber.
        mom_cond_1 = (exog[:, 0] - endog) ** 2 - (
            (tau[1] / tau[0]) ** (2 * param)
        ) * (exog[:, 1] - endog) ** 2
        mom_cond_2 = (exog[:, 1] - endog) ** 2 - (
            (tau[2] / tau[1]) ** (2 * param)
        ) * (exog[:, 2] - endog) ** 2

        # Additional moment conditions created by instruments
        list_mom_conds: list[np.ndarray] = []
        for i in range(0, 7):
            list_mom_conds.append(mom_cond_1 * inst[:, i])
            list_mom_conds.append(mom_cond_2 * inst[:, i])

        mom_conds = np.column_stack(list_mom_conds)

        return mom_conds
