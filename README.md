# README and Guidance

## Overview

The code files in this replication package construct the output in Nagel (2024) using Python. The `__main__.py` file runs all the code to generate the 5 figures and 4 tables. A replicator should expect the code to run for approximately 5 days. See the [documentation](https://htmlpreview.github.io/?https://github.com/michael-nagel/pfd/blob/main/docs/_build/html/index.html) for detailed information on the underlying code.

## Data Availability and Provenance Statements

### Statement about Rights

- [x] I certify that the author(s) of the manuscript have legitimate access to and permission to use the data used in this manuscript.

- [ ] I certify that the author(s) of the manuscript have documented permission to redistribute/publish the data contained within this replication package. Appropriate permission are documented in the [LICENSE](https://htmlpreview.github.io/?https://github.com/michael-nagel/pfd/blob/main/LICENSE) file.

### Summary of Availability

- [x] All data **are** publicly available.

- [ ] Some data **cannot be made** publicly available.

- [ ] **No data can be made** publicly available.

  | Data.Name      | Data.Files   | Location | Provided | Citation |
  | -------------- | ------------ | -------- | -------- | -------- |
  | "Alcohol Data" | alc_data.pkl | Data/    | TRUE     |          |

### Oddsportal Data


Datafiles:

- `data/raw/crawled_odds.json`
- `data/raw/crawled_urls.json`

## Dataset List

A detailed description of the data files' variables (long-form names, data type and description) in tablular form is provided in the codebook, which is part of this repository.

## Computational Requirements

Please strictly follow the steps outlined below to properly set up the project and environment required for replication. A Linux distribution (e.g., Ubuntu) or WSL(2) is required to run the code.

Clone the replication package that is available on GitHub using

    git clone https://github.com/michael-nagel/pfd.git

Setup the replication package by navigating to the repository directory and executing setup_pfd.txt

    cd pfd
    . setup_pfd.txt

The setup_pfd.txt file implements the following steps

- Create a virtual environment (venv)
- Activate the venv
- Install the `pfd` package into the venv

To replicate all the results, run the `__main__.py` file

    cd pfd/src/pfd
    python -m pfd

> [!WARNING]
> **If you install the package from the .whl or .tar.gz file**: Depending on your exact setup, it might be, that the system runs the scripts in your package installation path (e.g., `\\wsl.localhost\Ubuntu\home\username\.local\lib\python3.11\site-packages\pfd`) rather than the files in the cloned repository. In this case, you might want to delete the package in the exemplary path above to make changes to the scripts and run them.

### Controlled Randomness

The random seed is set in the configuration file `conf/config.yaml` where basic variables for all scripts are defined. If you want to change the random seed, use `conf/general/alt_seed.yaml`.

### Memory and Runtime Requirements

#### Summary

Approximate time needed to reproduce the analyses on a standard (2023) desktop machine:

- [ ] \<10 minutes

- [ ] 10-60 minutes

- [x] 1-2 hours

- [ ] 2-8 hours

- [ ] 8-24 hours

- [ ] 1-3 days

- [] 3-14 days

- [ ] \> 14 days

- [ ] Not feasible to run on a desktop machine, as described below.

#### Details

The code was last executed on a machine with the following features

- Linux distribution: Debian GNU/Linux 12 (bookworm)

- Architecture: x86/64

- CPU: Intel Broadwell 24 vCPU 12 cores

- RAM: 32 GB
