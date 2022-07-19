import asyncio
import hashlib
import json
import os
from typing import Any, Dict

import httpx


async def gather_with_concurrency(n, *tasks):
    """Gather but limit the number of concurrent tasks to n.
    From: https://stackoverflow.com/questions/48483348/how-to-limit-concurrency-with-python-asyncio
    """
    if n < 0:
        n = 100000
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task
    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def stream_download_file(url: str, outfile: str) -> None:
    """
    Stream file to disk without loading into memory 
    
    originally from 
    https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests

    Args:
        url (str): download from this url
        outfile (str): output to this url
    """
    dirname = os.path.dirname(outfile)
    os.makedirs(dirname, exist_ok=True)

    client = httpx.AsyncClient()
    async with client.stream("GET", url, timeout=1200) as r:
        r.raise_for_status()
        with open(outfile, 'wb') as f:
            async for data in r.aiter_bytes():
                f.write(data)

def dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    if len(dictionary) == 0:
        return ""
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()
