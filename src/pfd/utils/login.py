#!/usr/bin/env python3

# Imports

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

# Function


def login(
    service: Service, options: Options, my_username: str, my_password: str
) -> WebDriver:
    """
    Login to the website's account.

    Parameters
    ----------
    service : selenium.webdriver.chrome.service.Service
        Service parameter for the Chrome webdriver.
    options : selenium.webdriver.chrome.options.Options
        Options for configuring the Chrome webdriver.
    my_username : str
        Username for login.
    my_password : str
        Password for login.

    Returns
    -------
    selenium.webdriver.remote.webdriver.WebDriver
        Selenium webdriver instance.
    """
    # Start webdriver
    driver = webdriver.Chrome(service=service, options=options)

    # Log-in
    driver.get(url="https://www.oddsportal.com/login")
    time.sleep(1.5)

    try:
        username = driver.find_elements(by=By.ID, value="login-username-sign")[
            1
        ]
    except:
        username = driver.find_elements(by=By.ID, value="login-username-sign")[
            0
        ]

    password = driver.find_elements(by=By.ID, value="login-password-sign")[0]
    username.send_keys(my_username)
    password.send_keys(my_password)

    ele_to_click = driver.find_elements(
        by=By.CSS_SELECTOR, value=r".hover\:primary-btn-hover"
    )

    ele_to_click = [
        ele for ele in ele_to_click if ele.accessible_name == "Login"
    ]
    driver.execute_script("arguments[0].click();", ele_to_click[0])

    return driver
