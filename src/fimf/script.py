"""
Command line interface for autobrowser package
"""

from . import core


def main():
    if 0:
        from textual.cli.cli import run
        import sys

        sys.argv = f"textual run --dev {core.__file__}".split()
        sys.exit(run())
    else:

        # in the future there could be some commandline arguments here
        core.main()
