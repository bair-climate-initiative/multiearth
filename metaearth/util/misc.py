"""Miscellaneous utility functions."""
import functools
import hashlib
import json
import os
import shutil
from typing import Any, Dict
from urllib.parse import urlparse

import requests


def query_asset_size_from_download_url(download_url: str) -> int:
    """Query the size of the asset from the download url using an http request."""
    with requests.get(download_url, stream=True, timeout=10) as response:
        response.raise_for_status()
        if response.headers.get("Content-Length"):
            clen: str = response.headers.get("Content-Length", "")
            filesize_mb = int(clen) // 1024 // 1024
        else:
            filesize_mb = -1
    return filesize_mb


def stream_download(url: str, outfile: str) -> None:
    """Stream file to disk without loading into memory.

    originally from
    https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests

    Args:
        url (str): download from this url
        outfile (str): output to this url
    """
    dirname = os.path.dirname(outfile)
    os.makedirs(dirname, exist_ok=True)

    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        r.raw.read = functools.partial(r.raw.read, decode_content=True)
        with open(outfile, "wb") as f:
            shutil.copyfileobj(r.raw, f, length=16 * 1024 * 1024)


def dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    if len(dictionary) == 0:
        return ""
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


def sha256_hash(s: str) -> str:
    """Use SHA256 to hash a string.

    Args:
        s (str): An arbritrary string
    Returns:
        str: The hashed string
    """
    sha = hashlib.sha256()
    sha.update(s.encode())
    return sha.hexdigest()


def item_href_to_outfile(href: str, outdir: str) -> str:
    """Take an item and returns the output filename for it."""
    outname = os.path.basename(urlparse(href).path)
    if len(outname) > 64:
        outname = sha256_hash(outname)
    return os.path.join(outdir, outname)
