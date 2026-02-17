# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script sequentially executes all main files.
"""

# Imports

import hydra
from hydra.core.config_store import ConfigStore
from hydra.core.global_hydra import GlobalHydra

from pfd.features import shape_data
from pfd.models import run_estimation
from pfd.utils import Logger, PFDConfig
from pfd.visualization import create_descriptives

# Hydra Setup

cs = ConfigStore.instance()
cs.store(name="pfd_config", node=PFDConfig)

# Function


@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: PFDConfig) -> None:
    # Clear existing Hydra instance if any

    GlobalHydra.instance().clear()

    # Log File

    log = Logger.init_logger(name=__name__)
    t_start = Logger.get_time()

    # Run the main scripts in the correct sequential order

    shape_data()
    run_estimation()
    create_descriptives()

    # Execution Time and Log Finish

    log.info(f"Execution time: {Logger.get_exec_time(start_time=t_start)}")


if __name__ == "__main__":
    main()
