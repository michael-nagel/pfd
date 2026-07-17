#!/usr/bin/env python3

"""
This file crawls the data from the match links.
"""

# Imports

import json
import re
import time
from pathlib import Path

import hydra
import pandas as pd
from fake_useragent import UserAgent
from hydra.core.config_store import ConfigStore
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from pfd.utils import (
    Logger,
    PFDConfig,
    crawl_match_urls,
    login,
    set_options,
    set_user_agent,
)

# Hydra Setup

cs = ConfigStore.instance()
cs.store(name="pfd_config", node=PFDConfig)

# Function


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def _crawl_data(cfg: PFDConfig) -> None:
    # Logging

    log = Logger.init_logger(name=__name__)
    t_start = Logger.get_time()

    # External Files

    with open(f"{cfg.paths.acc}{cfg.files.cred}") as f:
        creds = json.load(f)

    file = Path(f"{cfg.paths.data_raw}crawled_urls.txt")
    if file.is_file():
        with open(f"{cfg.paths.data_raw}crawled_urls.txt") as f:
            crawled_match_urls = f.read().splitlines()
            f.close()
    else:
        crawled_match_urls = []

    # Webdriver Setup

    service = Service(executable_path=f"{cfg.paths.acc}{cfg.files.chrm_driv}")

    ua = UserAgent()
    user_agents = ua.random

    options = set_options(
        acpt_cookies_path=f"{cfg.paths.acc}{cfg.files.acpt_cookies}",
        user_agent=set_user_agent(user_agents=user_agents),
        headless=cfg.scraping.headless,
    )

    # Scraping

    while pd.Timestamp.now() <= pd.Timestamp(ts_input=cfg.scraping.crawl_till):
        driver = login(
            service=service,
            options=options,
            my_username=creds["username"],
            my_password=creds["password"],
        )
        driver.get(url="https://www.oddsportal.com/tennis/")
        time.sleep(2)
        tourn_urls = driver.find_elements(
            by=By.CSS_SELECTOR, value=".border-black-borders .text-black-main"
        )
        tourn_urls = [
            tourn_url.get_attribute("href") for tourn_url in tourn_urls
        ]
        tourn_urls = [tourn_url for tourn_url in tourn_urls if tourn_url]

        driver.quit()

        first_crawl = pd.Timestamp.now()

        while (
            pd.Timedelta(value=pd.Timestamp.now() - first_crawl).total_seconds()
            / 3600
        ) <= cfg.scraping.repeat_per:
            driver = login(
                service=service,
                options=options,
                my_username=creds["username"],
                my_password=creds["password"],
            )
            match_urls_tot: list[str] = []

            for tourn_url in tourn_urls:
                driver.get(url=tourn_url + r"\results")

                driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride",
                    {"userAgent": set_user_agent(user_agents=user_agents)},
                )

                time.sleep(1)

                try:
                    n_pages = driver.find_elements(
                        by=By.CSS_SELECTOR, value="#pagination"
                    )
                    n_pages = [ele.text for ele in n_pages if ele.text != ""][0]
                    n_pages = n_pages.rsplit(sep="\n")[-1]
                except:
                    n_pages = 1

                crawl_match_urls(driver=driver, match_urls_tot=match_urls_tot)

                page_counter = 2
                while page_counter <= int(n_pages):
                    driver.get(
                        url=tourn_url + rf"results/#/page/{page_counter}/"
                    )
                    driver.refresh()
                    crawl_match_urls(
                        driver=driver, match_urls_tot=match_urls_tot
                    )
                    page_counter += 1

            match_urls_temp = [
                url for url in match_urls_tot if url not in crawled_match_urls
            ]

            # Crawl

            for url in match_urls_temp:
                try:
                    driver.get(url=url)

                    driver.execute_cdp_cmd(
                        "Network.setUserAgentOverride",
                        {"userAgent": set_user_agent(user_agents=user_agents)},
                    )

                    time.sleep(1)

                    try:
                        login_check = driver.find_element(
                            by=By.CSS_SELECTOR,
                            value=r".border-b+ .hover\:primary-btn-hover"
                            r" .max-sm\:px-2",
                        ).text
                    except:
                        login_check = ""

                    if "CLICK TO SHOW MORE BOOKMAKERS" in login_check:
                        driver.quit()
                        driver = login(
                            service=service,
                            options=options,
                            my_username=creds["username"],
                            my_password=creds["password"],
                        )
                        driver.get(url=url)
                        time.sleep(1)

                    res = driver.find_elements(
                        by=By.CSS_SELECTOR, value="div.flex.flex-wrap"
                    )
                    res = [
                        ele.text
                        for ele in res
                        if ele.text.startswith("Final result")
                    ][0]

                    with open("../Data/crawled_urls.txt", "a+") as outfile:
                        outfile.write(url + "\n")

                    if res:
                        crawled_match_urls.append(url)

                        try:
                            data = {}

                            data["Encounter"] = driver.find_element(
                                by=By.CSS_SELECTOR,
                                value=r".max-mt\:\!hidden p",
                            ).text

                            data["Timestamp"] = str(pd.Timestamp.now())

                            date = driver.find_elements(
                                by=By.CSS_SELECTOR, value=".item-center p"
                            )
                            date = [ele.text for ele in date if ele.text != ""]
                            data["Date"] = " ".join(date)

                            data["Country"] = url.split("/", maxsplit=-1)[
                                4
                            ].capitalize()

                            data["Tournament"] = url.split("/", maxsplit=-1)[
                                5
                            ].replace("-", " ")

                            data["Result"] = res

                            bookies = driver.find_elements(
                                by=By.CSS_SELECTOR, value=r".max-mm\:hidden"
                            )
                            data["Bookies"] = [ele.text for ele in bookies]

                            payout = driver.find_elements(
                                by=By.CSS_SELECTOR,
                                value=r".text-black-main .text-\[10px\]",
                            )
                            data["Payout"] = [ele.text for ele in payout]

                            try:
                                odds_to_hover = driver.find_elements(
                                    by=By.CSS_SELECTOR,
                                    value=r".text-\[\#2F2F2F\] .gap-\[3px\]",
                                )

                                if (
                                    len(bookies)
                                    == len(payout)
                                    == len(odds_to_hover) / 2
                                ):
                                    odds_home = []
                                    odds_away = []

                                    for j in range(0, len(odds_to_hover)):
                                        driver.execute_script(
                                            "window.scrollBy(0, 20);"
                                        )
                                        time.sleep(0.2)

                                        ActionChains(
                                            driver=driver
                                        ).move_to_element(
                                            to_element=odds_to_hover[j]
                                        ).perform()

                                        odds = driver.find_element(
                                            by=By.CSS_SELECTOR,
                                            value="div.flex.flex-col.gap-2",
                                        )

                                        if (j % 2) == 0:
                                            odds_home.append(odds.text)
                                        else:
                                            odds_away.append(odds.text)

                                    data["OddsHome"] = odds_home
                                    data["OddsAway"] = odds_away
                            except:
                                pass

                            scroll_into_view = driver.find_elements(
                                by=By.CSS_SELECTOR, value=r"p.text-xs"
                            )
                            try:
                                scroll_into_view = [
                                    ele
                                    for ele in scroll_into_view
                                    if ele.text == "Betting Exchanges"
                                ]
                                driver.execute_script(
                                    "arguments[0].scrollIntoView();",
                                    scroll_into_view[0],
                                )
                            except:
                                pass
                            time.sleep(0.5)

                            try:
                                exng = driver.find_elements(
                                    by=By.CSS_SELECTOR,
                                    value=".text-black-main.font-main",
                                )
                                exng = [
                                    ele.text
                                    for ele in exng
                                    if ele.text == "Betfair Exchange"
                                    or ele.text == "Matchbook"
                                    or ele.text == "Smarkets"
                                ]
                                data["Exng"] = exng

                                if exng:
                                    payout_exng = driver.find_elements(
                                        by=By.CSS_SELECTOR,
                                        value=r".min-w-\[60px\] .flex-center "
                                        r".height-content.text-\[10px\]",
                                    )
                                    try:
                                        payout_exng = [
                                            ele.text
                                            for ele in payout_exng
                                            if "ODDS" not in ele.text
                                        ]
                                    except:
                                        pass

                                    data["PayoutExng"] = payout_exng

                                    prices_to_hover = driver.find_elements(
                                        by=By.CSS_SELECTOR,
                                        value=r".max-sm\:min-w-\[55px\]"
                                        r".min-h-\[50px\]",
                                    )
                                    prices_to_hover = [
                                        ele
                                        for ele in prices_to_hover
                                        if re.match(r"\d+", ele.text)
                                    ]

                                    if (
                                        len(exng) * 2
                                        == len(payout_exng)
                                        == len(prices_to_hover) / 2
                                    ):
                                        prices_back_home = []
                                        prices_back_away = []
                                        prices_lay_home = []
                                        prices_lay_away = []

                                        for k in range(0, len(prices_to_hover)):
                                            ActionChains(
                                                driver=driver
                                            ).move_to_element(
                                                to_element=prices_to_hover[k]
                                            ).perform()
                                            prices = driver.find_elements(
                                                by=By.CSS_SELECTOR,
                                                value=(
                                                    "div.flex.flex-col.gap-2"
                                                ),
                                            )

                                            prices = [
                                                ele.text
                                                for ele in prices
                                                if "Opening odds" in ele.text
                                            ]

                                            if (k % 2) == 0 and (k % 4) == 0:
                                                prices_back_home.append(prices)
                                            elif (k % 2) == 0:
                                                prices_lay_home.append(prices)
                                            elif ((k - 1) % 2) == 0 and (
                                                (k - 1) % 4
                                            ) == 0:
                                                prices_back_away.append(prices)
                                            else:
                                                prices_lay_away.append(prices)

                                        data["PriceBackHome"] = prices_back_home
                                        data["PriceBackAway"] = prices_back_away
                                        data["PriceLayHome"] = prices_lay_home
                                        data["PriceLayAway"] = prices_lay_away
                            except:
                                pass

                            # Append new data to total data

                            with open(
                                f"{cfg.paths.data_raw}crawled_odds.json", "a+"
                            ) as outfile:
                                json.dump(data, outfile)
                                outfile.write("\n")
                        except:
                            pass
                except:
                    pass

            driver.quit()

            time.sleep(cfg.scraping.sleep * 3600)

    # Execution Time and Log File Finish

    log.info(f"Execution time: {Logger.get_exec_time(start_time=t_start)}")


if __name__ == "__main__":
    _crawl_data()
