#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Imports

from pfd.utils import NumFormat

# Function


def save_values(
    key: str, value: float, file_name: str, fmt: str | None = None
) -> None:
    """
    Save tex values

    This function saves values in a .dat file for automatic use in tex
    files.

    Parameters
    ----------
    key : str
        Name of the value that is supposed to be saved.
    value : float
        Value that is supposed to be saved.
    file_name : str
        File name.
    fmt : str | None, default None
        Format of the value.
    """
    new_line = (
        f"{key};{f'{{:{fmt}}}'.format(value)}\n"
        if fmt
        else f"{key};{NumFormat.format_num(in_val=value)}\n"
    )

    updated = False
    try:
        with open(file=file_name, mode="r+") as file:
            lines = file.readlines()
            file.seek(0)
            for line in lines:
                if line.startswith(key + ";"):
                    file.write(new_line)
                    updated = True
                else:
                    file.write(line)

            if not updated:
                file.write(new_line)
            file.truncate()

    except FileNotFoundError:
        with open(file=file_name, mode="w") as file:
            file.write(new_line)
