"""API for downloading assets programmatically. Use cli.py to download assets from command line."""

import os
import sys
from datetime import date
from multiprocessing import JoinableQueue, Process, Queue
from queue import Empty
from time import sleep
from typing import Any, Dict, List, Tuple

import geopandas as gpd
from loguru import logger
from omegaconf import OmegaConf
from tqdm.asyncio import tqdm
from tqdm.contrib.concurrent import thread_map

from metaearth.config import ConfigSchema, get_collection_val_or_default
from metaearth.provider import get_provider
from metaearth.provider.base import BaseProvider
from metaearth.util.stac import (
    ExtractAsset,
    ExtractAssetCollection,
    extract_assets_from_item,
)


def _download_worker_task(
    q: "JoinableQueue[ExtractAsset]",
    done_q: "Queue[ExtractAsset]",
    err_q: "Queue[Tuple[ExtractAsset, Exception]]",
    num_retries: int,
) -> None:
    """Worker task for downloading assets."""
    while True:
        ast = q.get()
        try:
            ast.download()
            done_q.put(ast)
        except Exception as ex:
            if ast.download_attempts < num_retries:
                logger.debug(
                    f"Will retry ({ast.download_attempts}/{num_retries} attempts so far): "
                    + f"\nEncountered error while downloading {ast}: {ex}"
                )

                # requeue the asset for retry
                q.put(ast)
            else:
                logger.error(f"===\nFailed to download {ast}:\n>>>\n {ex}\n")
                err_q.put((ast, ex))
        q.task_done()


def _create_download_workers_and_queues(
    num_workers: int, num_retries: int
) -> Tuple[
    "JoinableQueue[ExtractAsset]",
    "Queue[ExtractAsset]",
    "Queue[Tuple[ExtractAsset, Exception]]",
]:
    """Kick off the multiproc worker pool for downloading assets.

    Args:
        num_workers (int): number of workers to use
        num_retries (int): number of times to retry a download
    Returns:
        Tuple[JoinableQueue, Queue, Queue]:
          {Job queue, finished queue, failed queue} - queues for
                  communicating between workers and main process
    """
    job_q: "JoinableQueue[ExtractAsset]" = JoinableQueue()
    finished_q: "Queue[ExtractAsset]" = Queue()
    fail_q: "Queue[Tuple[ExtractAsset, Exception]]" = Queue()
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


def extract_assets(
    cfg: ConfigSchema,
) -> Tuple[ExtractAssetCollection, ExtractAssetCollection]:
    """Run the full MetaEarth asset extraction process.

    This is intentionally a very long function for now.
    As this library takes shape, it will be broken up into smaller functions.

    Args:
        cfg: a dict config object
    Returns:
        Tuple[ExtractAssetCollection, ExtractAssetCollection]:
            0: Assets that were successfully extracted
            1: Assets that failed to extract (empty if all succeeded)
    """
    # string to identify the run
    run_str = (
        f"{'-'.join(sorted(cfg.collections.keys()))}_{date.today():%H:%M-%m-%d-%Y}"
    )

    # create output log dir if not exists
    if not os.path.exists(cfg.system.log_outdir):
        os.makedirs(cfg.system.log_outdir)

    # set logging level and log output
    logger.remove()
    logger.add(
        sys.stderr,
        format="{time:HH:mm:ss} {level} {message}",
        level=cfg.system.log_level,
        colorize=True,
    )
    log_output_file = os.path.join(cfg.system.log_outdir, f"{run_str}.log")
    logger.add(
        log_output_file,
        format="{time:HH:mm:ss} {level} {message}",
        level=cfg.system.log_level,
    )

    # write the config to file
    yaml_cfg = OmegaConf.to_yaml(cfg)
    with open(os.path.join(cfg.system.log_outdir, f"{run_str}_cfg.yaml"), "w") as f:
        f.write(str(yaml_cfg))

    # Process:
    # 1. For each collection, extract STAC item collection for given region
    # 2. In parallel, extract data from STAC item collection and write to
    # local/remote storage (this can simulataneously use multiple providers)
    # 3. Postprocess/plugins

    # prepare all collections
    logger.debug("Preparing collections")
    aoi_cache = {}
    extract_assets = ExtractAssetCollection()
    for collection_name in cfg.collections.keys():
        logger.debug(f"Preparing collection {collection_name}")

        # get the provider
        pvdr_dict: Dict[str, Any] = get_collection_val_or_default(
            cfg, collection_name, "provider"
        )
        pvdr: BaseProvider = get_provider(pvdr_dict["name"], **pvdr_dict["kwargs"])

        # get all other relevant config values
        datetime_range_str: str = get_collection_val_or_default(
            cfg, collection_name, "datetime"
        )
        aoi_file: str = get_collection_val_or_default(cfg, collection_name, "aoi_file")
        assets: List[str] = get_collection_val_or_default(
            cfg, collection_name, "assets"
        )
        max_items: int = get_collection_val_or_default(
            cfg, collection_name, "max_items"
        )

        # make sure output dir exists for later writing
        output_dir = get_collection_val_or_default(cfg, collection_name, "outdir")
        os.makedirs(output_dir, exist_ok=True)

        logger.info(
            f"Extraction details for collection {collection_name}:"
            + f"\n\t\tprovider=<{pvdr}> \n\t\ttimerange=<{datetime_range_str}>,"
            + f"\n\t\taoi_file=<{aoi_file}>, \n\t\toutput_dir=<{output_dir}>,"
            + f"\n\t\tassets=<{assets}>"
        )

        logger.debug(f"loading area of interest file: {aoi_file}")
        if aoi_file not in aoi_cache:
            aoi_cache[aoi_file] = gpd.read_file(aoi_file).unary_union
        region = aoi_cache[aoi_file]

        # find the assets to be extracted
        itm_set = list(
            pvdr.region_to_items(region, datetime_range_str, collection_name, max_items)
        )

        # create a set of extraction tasks for each item in each provider
        # below, before attempting extraction, we check if each item is already/currently
        # extracting from another provider and skip if so
        logger.info(
            f"\n{pvdr} returned {len(itm_set)} items for {collection_name} "
            + f"for datetime {datetime_range_str}\n"
        )

        logger.debug(f"Adding item assets from {pvdr} to extraction tasks")
        for itm in itm_set:
            extract_assets += extract_assets_from_item(itm, pvdr, assets, output_dir)

    # we may need to query the size of the assets, which we use for logging
    # and as an imperfect way to check the validity of the downloaded data
    logger.debug("Checking asset sizes")
    asts_with_unknown_filesize = []
    for ast in extract_assets:
        if ast.filesize_unknown():
            asts_with_unknown_filesize.append(ast)

    if len(asts_with_unknown_filesize) > 0:
        if cfg.system.query_asset_sizes:
            logger.info(
                f"{len(asts_with_unknown_filesize):,} assets did not specify file size, "
                + "will query size directly with http get request (this may take a few moments)\n"
                + "system.query_asset_sizes=False can be used to disable this behavior"
            )
            thread_map(
                lambda ast: ast.query_asset_size_from_download_url(),
                asts_with_unknown_filesize,
                max_workers=cfg.system.max_concurrent_extractions,
            )

    # print a nice summary (depends on log level how detailed it is)
    logger.info(
        f"{len(extract_assets):,} assets to extract from {len(itm_set):,} items"
    )
    extract_assets.summary()

    # kick off the extraction tasks
    if cfg.system.dry_run:
        logger.info("Dry run, not extracting anything")
        return ExtractAssetCollection(), ExtractAssetCollection()

    # spin up multiproc workers and return queues
    # job_q: queue assets to be extracted
    # finished_q: queue assets that have been extracted
    # fail_q: queue assets that failed to extract
    job_q, finished_q, fail_q = _create_download_workers_and_queues(
        cfg.system.max_concurrent_extractions, cfg.system.max_download_attempts
    )

    logger.info("Starting data extraction")
    exists_ct = 0
    removed_ct = 0
    added_ct = 0
    download_asset_size = 0
    for ast in extract_assets:
        if os.path.exists(ast.outfile):
            # check if the size of the file is as expected, else remove
            skip = True
            if cfg.system.remove_existing_if_wrong_size:
                mb_size = os.path.getsize(ast.outfile) // 1e6
                if ast.filesize_mb > 0 and max(1, abs(mb_size - ast.filesize_mb)) > 1:
                    logger.info(
                        f"Removing {ast.outfile} because it is {mb_size:,}MB"
                        + f"instead of {ast.filesize_mb:,}MB"
                    )
                    os.remove(ast.outfile)
                    removed_ct += 1
                    skip = False
                else:
                    logger.info(
                        "The following file is the wrong size, "
                        + "but cfg.system.remove_existing_if_wrong_size"
                        + f"is not set to true, so will not remove: {ast.outfile}"
                    )

            if skip:
                logger.debug(f"Skipping {ast.outfile}, exists")
                exists_ct += 1
                continue

        # add to pool of tasks to run in parallel
        job_q.put(ast)
        download_asset_size += ast.filesize_mb
        added_ct += 1

    if removed_ct > 0:
        logger.info(
            f"Removed {removed_ct:,} files that may not be fully downloaded or corrupt"
        )

    if exists_ct > 0:
        logger.info(f"{exists_ct:,} assets already exist, skipping")

    if added_ct == 0:
        logger.info("No assets to extract")
    else:
        logger.info(f"Extracting {added_ct:,} assets ({download_asset_size:,}MB)...")

    # show progress bar
    completed_assets = ExtractAssetCollection()
    with tqdm(total=download_asset_size, desc="MB downloaded") as pbar:
        while True:
            try:
                completed_ast = finished_q.get(timeout=5)
                completed_assets.add_asset(completed_ast)
                pbar.update(completed_ast.filesize_mb)
            except Empty:
                # it's possible all extractions error'd out, and the queue would never return,
                # so check periodically (after timeout)
                pass

            # TODO figure out how to do this without relying on internals
            if job_q._unfinished_tasks._semlock._is_zero():  # type: ignore
                pbar.update(completed_ast.filesize_mb)
                break
            sleep(1)

    job_q.join()

    # Log the failed extractions to a file
    error_assets = ExtractAssetCollection()
    if not fail_q.empty():
        fail_file = os.path.join(cfg.system.log_outdir, f"{run_str}_failed.log")
        with open(fail_file, "w") as f:
            while not fail_q.empty():
                ast, ex = fail_q.get()
                error_assets.add_asset(ast)
                f.write(f"{ast} <{ex}>\n")
        logger.warning(
            f"Failed to download {len(error_assets)} assets: logged failed assets to {fail_file}"
        )
    fail_q.close()

    return (completed_assets, error_assets)
