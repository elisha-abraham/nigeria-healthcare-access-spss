"""Run the SPSS syntax without opening SPSS.

Use the Python that ships with SPSS Statistics, which can talk to the SPSS engine:

    "C:\\Program Files\\IBM\\SPSS\\Statistics\\27\\statisticspython3.bat" scripts/run_spss.py

With no arguments it runs syntax/00_run_all.sps. Name one or more syntax files
to run only those (the macros are always loaded first):

    ... scripts/run_spss.py syntax/01_prepare_data.sps

Add --keep-going to carry on after an error, which makes SPSS print every
error message instead of stopping at the first.

SPSS prints its output as text; redirect it to a file to keep it.
"""
import sys
from pathlib import Path

import spss

ROOT = Path(__file__).resolve().parent.parent


def main():
    arguments = sys.argv[1:]
    on_error = "CONTINUE" if "--keep-going" in arguments else "STOP"
    steps = [argument for argument in arguments if argument != "--keep-going"]
    insert = "INSERT FILE = '{}' ERROR = " + on_error + " CD = NO."
    spss.Submit("CD '{}'.".format(ROOT.as_posix()))
    if not steps:
        spss.Submit(insert.format("syntax/00_run_all.sps"))
    else:
        spss.Submit(insert.format("syntax/macros.sps"))
        for step in steps:
            spss.Submit(insert.format(step))
    spss.StopSPSS()


if __name__ == "__main__":
    main()
