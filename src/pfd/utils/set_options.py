#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Function


def set_options(
    acpt_cookies_path: str, user_agent: str, headless: bool
) -> Options:
    """
    Define the options for the webdriver.

    Parameters
    ----------
    acpt_cookies_path: str
        Path of "I-don-t-care-about-cookies.crx" file
    user_agent : str
        Fake user agent.
    headless : bool
        Headless mode.

    Returns
    -------
    selenium.webdriver.chrome.options.Options
        Options for configuring the Chrome webdriver.
    """
    # Define options

    options = webdriver.ChromeOptions()

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-sh-usage")
    options.add_argument("--blink-settings=imagesEnabled=false")

    if headless:
        options.add_argument("headless")
    else:
        options.add_argument(argument="window-size=1320,1080")

        options.add_extension(extension=acpt_cookies_path)

    # Fake user agent

    options.add_argument(argument=f"user-agent={user_agent}")

    return options
