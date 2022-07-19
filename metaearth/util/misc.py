"""Miscellaneous utility functions."""
import functools
import hashlib
import json
import os
import shutil
from typing import Any, Dict

import requests


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
