#!/usr/bin/env python3

# %% Imports

import unittest

import numpy as np
import pandas as pd
import pymc as pm

from pfd.helpers.base import create_pm_mod
from pfd.utils import (
    NumFormat,
    calc_rmse,
    calc_win_props,
    enc_categ_var,
    pivot_df,
    scale_vars,
)

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

    def test_format_num_rounds_small_values_to_four_decimals(self) -> None:
        """
        Check that values between 0.0001 and 1 are formatted to four
        decimal places.
        """
        self.assertEqual("0.1235", NumFormat.format_num(in_val=0.123456))

    def test_enc_categ_var_encodes_and_drops_original(self) -> None:
        """
        Check that categorical encoding creates the expected dummy
        column and removes the original categorical column.
        """
        df = pd.DataFrame(
            {
                "Competition": ["ATP", "WTA", "ATP", "WTA"],
                "Value": [1, 2, 3, 4],
            }
        )

        df_enc = enc_categ_var(
            df=df,
            col="Competition",
            prefix="Compet",
            rm_first=True,
            rm_categ_var=True,
        )

        self.assertNotIn("Competition", df_enc.columns)
        self.assertIn("Compet_WTA", df_enc.columns)
        self.assertListEqual(list(df_enc["Compet_WTA"]), [0, 1, 0, 1])

    def test_scale_vars_standardizes_to_zero_mean_unit_std(self) -> None:
        """
        Check that scale_vars returns data with zero mean and unit
        standard deviation.
        """
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0]).reshape(-1, 1)

        scaled = scale_vars(x)

        self.assertAlmostEqual(scaled.mean(), 0.0, places=8)
        self.assertAlmostEqual(scaled.std(), 1.0, places=8)

    def test_calc_rmse_matches_manual_calculation(self) -> None:
        """
        Check that calc_rmse returns the manually computed RMSE.
        """
        y_true = pd.Series([1.0, 2.0, 3.0])
        y_pred = pd.Series([1.0, 2.0, 4.0])

        rmse = calc_rmse(y_true, y_pred)

        self.assertAlmostEqual(rmse, np.sqrt(1 / 3))

    def test_calc_win_props_counts_matches_in_interval(self) -> None:
        """
        Check that calc_win_props filters on the given interval and
        computes the winning proportion of the filtered rows.
        """
        df = pd.DataFrame(
            {
                "DltOpnCls": [0.01, 0.02, 0.05, -0.01],
                "Match": [1, 0, 1, 1],
                "NumOddsMvt": [5, 6, 7, 8],
            }
        )

        _, _, _, n_matches, win_prop, _, _ = calc_win_props(
            df=df, ival=[0, 0.03]
        )

        self.assertEqual(n_matches, 2)
        self.assertAlmostEqual(win_prop, 0.5)

    def test_calc_win_props_raises_on_mixed_sign_interval(self) -> None:
        """
        Check that calc_win_props rejects intervals that mix signs.
        """
        df = pd.DataFrame(
            {"DltOpnCls": [0.01], "Match": [1], "NumOddsMvt": [5]}
        )

        with self.assertRaises(ValueError):
            calc_win_props(df=df, ival=[-0.01, 0.01])

    def test_pivot_df_reshapes_long_to_wide(self) -> None:
        """
        Check that pivot_df reshapes long-format odds movements into
        one column per period.
        """
        df = pd.DataFrame(
            {
                "Matchup": [0, 0],
                "Bookies": ["Pinnacle", "Pinnacle"],
                "CumCount": [0, 1],
                "OddsMvt": [0.5, 0.6],
            }
        )

        df_wide = pivot_df(df=df, exog_cols=[], n_per=2)

        self.assertIn("OddsMvt0", df_wide.columns)
        self.assertIn("OddsMvt1", df_wide.columns)
        self.assertEqual(df_wide.loc[0, "OddsMvt0"], 0.5)
        self.assertEqual(df_wide.loc[0, "OddsMvt1"], 0.6)


if __name__ == "__main__":
    unittest.main()
