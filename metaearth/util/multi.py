"""Multiprocessing utilities."""

from multiprocessing import JoinableQueue, Process, Queue
from typing import Tuple

from loguru import logger

from ..assets import DownloadWrapper


def _download_worker_task(
    q: "JoinableQueue[DownloadWrapper]",
    done_q: "Queue[DownloadWrapper]",
    err_q: "Queue[Tuple[DownloadWrapper, Exception]]",
    num_retries: int,
) -> None:
    """Worker task for downloading assets."""
    while True:
        dwrap = q.get()
        try:
            dwrap.download_attempts += 1
            dwrap()
            done_q.put(dwrap)
        except Exception as ex:
            if dwrap.download_attempts < num_retries:
                logger.debug(
                    f"Will retry ({dwrap.download_attempts}/{num_retries} attempts so far): "
                    + f"\nEncountered error while downloading {dwrap}: {ex}"
                )
                # requeue the asset for retry
                q.put(dwrap)
            else:
                logger.error(f"===\nFailed to download {dwrap}:\n>>>\n {ex}\n")
                err_q.put((dwrap, ex))
        q.task_done()


def create_download_workers_and_queues(
    num_workers: int, num_retries: int
) -> Tuple[
    "JoinableQueue[DownloadWrapper]",
    "Queue[DownloadWrapper]",
    "Queue[Tuple[DownloadWrapper, Exception]]",
]:
    """Kick off the multiproc worker pool for downloading assets.

    See stac.py:_download for example usage.

    Args:
        num_workers (int): number of workers to use
        num_retries (int): number of times to retry a download
    Returns:
        Tuple[JoinableQueue, Queue, Queue]:
          {Job queue, finished queue, failed queue} - queues for
                  communicating between workers and main process
    """
    job_q: "JoinableQueue[DownloadWrapper]" = JoinableQueue()
    finished_q: "Queue[DownloadWrapper]" = Queue()
    fail_q: "Queue[Tuple[DownloadWrapper, Exception]]" = Queue()
    workers = [
        Process(
            target=_download_worker_task,
            args=(job_q, finished_q, fail_q, num_retries),
            daemon=True,
        )
        for _ in range(num_workers)
    ]
    for p in workers:
        p.start()

    return job_q, finished_q, fail_q
