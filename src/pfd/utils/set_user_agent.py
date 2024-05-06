#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from random import randint
from typing import Any

# Function


def set_user_agent(user_agents: Any | str) -> str:
    """
    Set the random user agent for the webdriver.

    Parameters
    ----------
    user_agents : Any | str
        Fake user agents.

    Returns
    -------
    str
        User agent.
    """
    if not isinstance(user_agents, str):
        user_agents = user_agents[randint(0, len(user_agents) - 1)]

    return user_agents
