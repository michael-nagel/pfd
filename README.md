# README and Guidance

## Overview

The code files in this replication package construct the output in Nagel (2024) using Python. The `__main__.py` file runs all the code to generate the 27 figures and 9 tables. A replicator should expect the code to run for approximately 3 hours. See the [documentation](https://htmlpreview.github.io/?https://github.com/michael-nagel/pfd/blob/main/docs/_build/html/index.html) for detailed information on the underlying code.

## Data Availability and Provenance Statements

### Statement about Rights

- [x] I certify that the author(s) of the manuscript have legitimate access to and permission to use the data used in this manuscript.

- [x] I certify that the author(s) of the manuscript have documented permission to redistribute/publish the data contained within this replication package. Appropriate permission are documented in the [LICENSE](https://htmlpreview.github.io/?https://github.com/michael-nagel/pfd/blob/main/LICENSE) file.

### Summary of Availability

- [x] All data **are** publicly available.

- [ ] Some data **cannot be made** publicly available.

- [ ] **No data can be made** publicly available.

### Details on each Data Source

  | Data.Name    | Data.Files       | Location     | Provided | Citation |
  | ------------ | ---------------- | ------------ | -------- | -------- |
  | "Oddsportal" | crawled_odds.txt | data/raw/    | TRUE     |          |
  |              | crawled_urls.txt | data/raw/    | TRUE     |          |

### Oddsportal Data

Datafiles:

We continuously scraped data from Oddsportal over the period from March 2023 to November 2023. The corresponding code file is `_crawl_data`. This file cannot be executed anymore because we do not include the credentials to log in to our Oddsportal account in the repository. Additionally, the webpage may have changed, rendering the provided code non-functional.

- `data/raw/crawled_odds.json`
- `data/raw/crawled_urls.json`

## Dataset List

A detailed description of the data files' variables (long-form names, data type and description) in tablular form is provided in the codebook, which is part of this repository.

## Computational Requirements

Please strictly follow the steps outlined below to properly set up the project and environment required for replication. A Linux distribution (e.g., Ubuntu) or WSL(2) is required to run the code (PyMC/nutpie compile more reliably there than on native Windows).

Clone the replication package that is available on GitHub using

    git clone https://github.com/michael-nagel/pfd.git

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't already have it, then set up the environment by navigating to the repository directory and running

    cd pfd
    uv sync --all-groups

This creates a `.venv` and installs the `pfd` package (editable) along with its runtime, dev (`pytest`, `ruff`, `ty`) and docs (`sphinx`) dependencies, pinned via `uv.lock`.

To replicate all the results, run the `__main__.py` file from the repository root

    uv run python -m pfd

A `Makefile` bundles the common commands:

    make sync       # uv sync --all-groups
    make lint       # ruff check
    make format     # ruff format
    make typecheck  # ty check
    make test       # pytest with coverage
    make check      # lint + typecheck + test

### Controlled Randomness

The random seed is set in the configuration file `conf/config.yaml` where basic variables for all scripts are defined. If you want to change the random seed, use `conf/general/alt_seed.yaml`.

### Memory and Runtime Requirements

#### Summary

Approximate time needed to reproduce the analyses on a standard (2024) desktop machine:

- [ ] \<10 minutes

- [ ] 10-60 minutes

- [ ] 1-2 hours

- [x] 2-8 hours

- [ ] 8-24 hours

- [ ] 1-3 days

- [] 3-14 days

- [ ] \> 14 days

- [ ] Not feasible to run on a desktop machine, as described below.

#### Details

The code was last executed on a machine with the following features:

- Linux distribution: WSL2 (Ubuntu)

- Architecture: x86/64

- CPU: Intel Broadwell 32 vCPU 16 cores

- RAM: 64 GB
