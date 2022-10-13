# /usr/bine/env python

"""
Prints files that do not load correctly using rasterio.

Example usage:

find /path/to/data -name '*.tif' | parallel --pipe -N 1 python util/verify-file.py
"""


import sys

import rasterio

if __name__ == "__main__":
    fname = sys.stdin.read().strip()
    try:
        fhandler = rasterio.open(fname).read()
    except Exception:
        print(fname)
