"""
Command line interface for autobrowser package
"""

import argparse
from ipydex import IPS, activate_ips_on_exception
from . import core

activate_ips_on_exception()


def main():
    # hacky version of the debug mode

    from textual.cli.cli import run
    import sys


    sys.argv = f"textual run --dev {core.__file__}".split()
    sys.exit(run())


def main1():

    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--helpq", help=f"show help", action="store_true")

    args = parser.parse_args()

    # in the future there could be some commandline arguments here
    core.main()
