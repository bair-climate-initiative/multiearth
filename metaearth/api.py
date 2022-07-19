import asyncio
import os
import sys
from datetime import date

import geopandas as gpd
from loguru import logger
from omegaconf import OmegaConf
from tqdm.asyncio import tqdm

from metaearth.config import ConfigSchema, get_collection_val_or_default
from metaearth.util.stac import (ExtractAssetCollection, extract_asset,
                                 extract_assets_from_item)

from metaearth.provider import get_provider


async def extract_assets(cfg: ConfigSchema) -> asyncio.coroutine:
    """
    Runs the full MetaEarth asset extraction process.
    This is intentionally a very long function for now. 
    As this library takes shape, it will be broken up into smaller functions.

    Args:
        cfg: a dict config object
    Returns:
        asyncio.coroutine: A coroutine that runs the asset extraction/download
    """

    # string to identify the run
    run_str = f"{'-'.join(sorted(cfg.collections.keys()))}_{date.today():%H:%M-%m-%d-%Y}"

    # create output log dir if not exists
    if not os.path.exists(cfg.system.log_outdir):
        os.makedirs(cfg.system.log_outdir)

    # set logging level and log output
    logger.remove()
    logger.add(sys.stderr, format="{time:HH:mm:ss} {level} {message}", level=cfg.system.log_level)
    log_output_file = os.path.join(cfg.system.log_outdir, f"{run_str}.log")
    logger.add(log_output_file, format="{time:HH:mm:ss} {level} {message}", level=cfg.system.log_level)

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
        pvdr_dict = get_collection_val_or_default(cfg, collection_name, "provider")
        pvdr = get_provider(pvdr_dict["name"], **pvdr_dict["kwargs"])
        
        # get all other relevant config values
        datetime_range_str = get_collection_val_or_default(cfg, collection_name, "datetime")
        aoi_file = get_collection_val_or_default(cfg, collection_name, "aoi_file")
        assets = get_collection_val_or_default(cfg, collection_name, "assets")
        
        # make sure output dir exists for later writing
        output_dir = get_collection_val_or_default(cfg, collection_name, "outdir")
        os.makedirs(output_dir, exist_ok=True)

        
        logger.info(f"Extraction details for collection {collection_name}:" + 
                    f"\n\t\tprovider=<{pvdr}> \n\t\ttimerange=<{datetime_range_str}>," + 
                    f"\n\t\taoi_file=<{aoi_file}>, \n\t\toutput_dir=<{output_dir}>, \n\t\tassets=<{assets}>")
        
        logger.debug(f"loading area of interest file: {aoi_file}")
        if aoi_file not in aoi_cache: 
            aoi_cache[aoi_file] = gpd.read_file(aoi_file).unary_union
        region = aoi_cache[aoi_file]

        # find the assets to be extracted
        itm_set = list(pvdr.region_to_items(region, datetime_range_str, collection_name))
        
        # create a set of extraction tasks for each item in each provider
        # below, before attempting extraction, we check if each item is already/currently
        # extracting from another provider and skip if so
        logger.info(f"\n{pvdr} return {len(itm_set)} items for {collection_name} for datetime {datetime_range_str}\n")
        
        logger.debug(f"Adding item assets from {pvdr} to extraction tasks")
        for itm in itm_set:
            extract_assets += extract_assets_from_item(itm, pvdr, assets, output_dir)
        
    # we may need to query the size of the assets, which we use for logging
    # and as an imperfect check validity of the downloaded data
    logger.debug("Checking asset sizes")
    unknown_filesize_ct = 0
    filesize_awaitables = []
    for ast in extract_assets:
        if ast.filesize_unknown():
            unknown_filesize_ct += 1
            durl = pvdr.asset_to_download_url(ast.asset)
            filesize_awaitables.append(ast.set_asset_size_from_download_url(durl))

    if unknown_filesize_ct > 0:
        logger.info(f"{unknown_filesize_ct:,} assets did not specify file size, will query size directly with http get request (this may take a few moments)")
        for aid in tqdm.as_completed(filesize_awaitables):
           await aid

    print(f"{len(extract_assets):,} assets to extract from {len(itm_set):,} items")

    # print a nice summary
    extract_assets.summary()

    # kick off the extraction tasks
    if cfg.system.dry_run:
        logger.info("Dry run, not extracting anything")
        return

    logger.info(f"Starting data extraction")

    exists_ct = 0
    removed_ct = 0
    tasks_asset_pairs = []
    for ast in extract_assets:
        if os.path.exists(ast.outfile):
            # check if the size of the file is as expected, else remove
            skip = True
            if cfg.system.remove_existing_if_wrong_size:
                mb_size = os.path.getsize(ast.outfile) // 1e6
                if ast.filesize_mb > 0 and max(1, abs(mb_size -  ast.filesize_mb)) > 1:
                    logger.info(f"Removing {ast.outfile} because it is {mb_size:,}MB instead of {ast.filesize_mb:,}MB")
                    os.remove(ast.outfile)
                    removed_ct += 1
                    skip = False
            else:
                logger.info("The following file is the wrong size, but cfg.system.remove_existing_if_wrong_size is not set to true, so will not remove: {ast.outfile}")

            if skip:
                logger.debug(f"Skipping {ast.outfile}, exists")
                exists_ct += 1
                continue
            
        tasks_asset_pairs.append((extract_asset(ast), ast))

    if removed_ct > 0:
        logger.info(f"Removed {removed_ct:,} files that may not be fully downloaded or corrupt")

    if exists_ct > 0:
        logger.info(f"{exists_ct:,} assets already exist, skipping")

    if len(tasks_asset_pairs) == 0:
        logger.info("No assets to extract")
        return

    retry_ct = 0
    failed_extractions = []
    while len(tasks_asset_pairs) > 0 and retry_ct < cfg.system.max_download_retries:
        potential_errors = await asyncio.gather(*[t[0] for t in tasks_asset_pairs], return_exceptions=True) #  gather_with_concurrency
        new_tasks = []
        for err, tsk in zip(potential_errors, tasks_asset_pairs):
            if err is not None and issubclass(err.__class__, Exception):
                if retry_ct + 1 == cfg.system.max_download_retries:
                    failed_extractions.append(tsk[1])
                else:
                    logger.warning(f"Exception encountered {err} - Retrying {tsk}")
                    new_tasks.append((extract_asset(tsk[1]), tsk[1]))
        tasks_asset_pairs = new_tasks
        retry_ct += 1
    
    if len(failed_extractions) > 0:
        logger.warning(f"Failed to extract the following { len(failed_extractions) } assets: { failed_extractions }")
        with open(os.path.join(cfg.system.log_outdir, f"{run_str}_failed.log"), "w") as f:
            f.write("\n".join([str(v) for v in failed_extractions]))
