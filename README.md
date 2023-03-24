[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# fimf – Find and Replace in Multiple Files


![fimf screenshot](doc/screenshot.png "screenshot of fimf: terminal application (text based ui) with 3 input fields, 3 buttons and other widgets")

## Development Status

This software was developed and tested with the [textual](textual.textualize.io/) framework in version 0.15.1.

## Caution

Though it might already be quite useful, fimf is currently still in "alpha" status, i.e., it is probably buggy. Please make a backup of your data files before manipulating them with fimf. Also, search-and-replace across many files can go wrong (due to bugs or due to user input) and there is **no undo button** in fimf.

## Installation

Development mode: Clone the repo and run `pip install -e .` from within that directory.

Normal usage mode: `pip install fimf`.


## Usage

Call `fimf` (the [textual](textual.textualize.io/) user interface (TUI) should be self-explanatory).


