#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from typing import Any, List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

# Function


def crawl_match_urls(driver: WebDriver, match_urls_tot: List[Any]) -> None:
    """
    Crawl match urls.

    This function crawls match urls from the target website.

    Parameters
    ----------
    driver : from selenium.webdriver.remote.webdriver.WebDriver
        Selenium webdriver instance.
    match_urls_tot : list
        List containing the total match urls crawled.
    Returs
    """
    match_urls = driver.find_elements(
        by=By.CSS_SELECTOR, value="a.border-black-borders"
    )
    match_urls = [match_url.get_attribute("href") for match_url in match_urls]
    match_urls_tot.extend(match_urls)
