#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# %% Imports

import unittest

import numpy as np
import pandas as pd
import pymc as pm

from pfd.helpers.base import create_pm_mod
from pfd.utils import NumFormat

# %% Class


class UnitTest(unittest.TestCase):
    def test_create_dhs_returns_pymc_model(self) -> None:
        """
        Perform unit test #1.

        Check if the returned object is an instance of PyMC Model.
        """
        # Create example data
        n_per = 50
        n_obs = 100
        cols = [f"OddsMvt{i}" for i in range(0, n_per)]
        df = pd.DataFrame(data=np.random.rand(n_obs, n_per), columns=cols)
        df["Bookies"] = np.repeat(["Pinnacle", "Marathonbet"], n_per)
        df["Match"] = np.random.choice([0, 1], size=n_obs, p=[0.5, 0.5])

        # Instatiate model
        model = create_pm_mod(df=df, n_per=n_per, incr=5)

        self.assertIsInstance(model, pm.Model)

    def test_formatting_behavior(self) -> None:
        """
        Perform unit test #3.

        Check if the formatted value equals target value.
        """

        self.assertEqual("1", NumFormat.format_num(in_val=1.00))


if __name__ == "__main__":
    unittest.main()
