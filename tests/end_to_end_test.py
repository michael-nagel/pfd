#!/usr/bin/env python3

# %% Imports

import os
import unittest

# %% Expected outputs

# These are the figures/tables the current shape_data -> run_estimation
# -> create_descriptives pipeline writes to reports/figures and
# reports/tables. Checking for the specific expected filenames (rather
# than just a count) catches renames/removals precisely instead of
# passing as long as *some* N files happen to exist.
#
# NOTE: this test only inspects whatever the reports/ directories
# already contain (e.g. from a prior full pipeline run) - it does not
# run the pipeline itself. run_estimation.py is still one large
# monolithic function (see the modernization plan), so driving a real
# end-to-end run from a test isn't practical yet. Once it's split into
# testable steps (Phase 3), this should be replaced with a test that
# actually runs shape_data -> run_estimation -> create_descriptives on
# a small dataset and checks the outputs it produces.

EXPECTED_FIGURES = {
    "crawling_process.pdf",
    "cs_mean_rtrn.pdf",
    "dist_bookies.pdf",
    "dist_impl_probs.pdf",
    "facetgrid_gamma_advi_tot.pdf",
    "facetgrid_gamma_nuts_tot.pdf",
    "gmm_jstat.pdf",
    "gmm_params.pdf",
    "gmm_pvalue.pdf",
    "hist_price_mvts.pdf",
    "hist_ts_dur.pdf",
    "imput_loss.pdf",
    "legend.pdf",
    "pacf.pdf",
    "post_gamma_nuts_fav_udd.pdf",
    "post_gamma_nuts_ivals.pdf",
    "post_gamma_nuts_pro_amat.pdf",
    "post_gamma_tot.pdf",
    "rmse.pdf",
    "rtrn_opn_cls.pdf",
    "scatter_gamma_loss.pdf",
    "traces_gamma_tot_1.pdf",
    "traces_gamma_tot_2.pdf",
    "tracker_advi.pdf",
    "unbiased_reg.pdf",
    "violin_opn_cls.pdf",
    "win_props_re.pdf",
}

EXPECTED_TABLES = {
    "desc_cat.tex",
    "desc_num.tex",
    "res_garch.tex",
    "res_gpm.tex",
    "res_pm_mod.tex",
    "res_rfa.tex",
    "res_rfa_tot.tex",
    "res_wp.tex",
    "res_wp_re.tex",
}


class EndToEndTest(unittest.TestCase):
    def test_expected_figures_are_present(self) -> None:
        """
        Perform end-to-end test #1.

        Check that every figure the pipeline is expected to write is
        present in reports/figures.
        """
        if not os.path.isdir("reports/figures"):
            self.skipTest(
                "reports/figures does not exist - run the "
                "pipeline first (python -m pfd)"
            )

        figs = set(os.listdir("reports/figures"))
        missing = EXPECTED_FIGURES - figs
        self.assertEqual(missing, set(), f"Missing figures: {missing}")

    def test_expected_tables_are_present(self) -> None:
        """
        Perform end-to-end test #2.

        Check that every table the pipeline is expected to write is
        present in reports/tables.
        """
        if not os.path.isdir("reports/tables"):
            self.skipTest(
                "reports/tables does not exist - run the "
                "pipeline first (python -m pfd)"
            )

        tabs = set(os.listdir("reports/tables"))
        missing = EXPECTED_TABLES - tabs
        self.assertEqual(missing, set(), f"Missing tables: {missing}")


if __name__ == "__main__":
    unittest.main()
