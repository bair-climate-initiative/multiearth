import base64
import hashlib
import os
import pickle

import geopandas as gpd
import hydra
from numpy import isin
import planetary_computer
import requests
import xarray
import xrspatial
from datashader.colors import Elevation
from datashader.transfer_functions import shade, stack
from loguru import logger
from omegaconf import DictConfig, OmegaConf
from pystac_client import Client

from metaearth.util.stac import region_to_stac_item_collection


# DEV testing - will clean up and organize once basically working
@hydra.main(version_base=None, config_path="./../../config", config_name="demo")
def main(cfg: DictConfig) -> None:
    """
    Args:
        cfg: a dict config object
    Returns:
        int: A return code
    Does stuff.
    """    
    
    # prepare a hashed representation of key config values (start time, end time, constellations
    coll_names = cfg.collections.keys()
    hash_vals = (
        "_".join(
            [cfg.start_date, cfg.end_date]
            + [coll for coll in coll_names]
            + [cfg.aoi],
        )
    ).encode("utf-8")

    hash_str_b = hashlib.md5(hash_vals).digest()
    hash_str = base64.urlsafe_b64encode(hash_str_b).decode("utf-8").rstrip("=")

    # create output dir if not exists
    if not os.path.exists(cfg.output):
        os.makedirs(cfg.output)
    
    # setup the caching outputs
    cfg.item_collection = os.path.join(
        cfg.output,
        f"{hash_str}_item_collection.geojson",
    )
    cfg.extraction_tasks = os.path.join(
        cfg.output,
        f"{hash_str}_extraction_tasks.pkl",
    )

    # write the config to file
    yaml_cfg = OmegaConf.to_yaml(cfg)
    with open(os.path.join(cfg.output, f"{hash_str}_cfg.yaml"), "w") as f:
        f.write(str(yaml_cfg))

    logger.info(f"Starting data extraction for cfg: {hash_str}")

    logger.debug(f"loading area of interest file: {cfg.aoi}")
    region = gpd.read_file(cfg.aoi).unary_union
    
    
    # Process:
    # 1. For each provider, extract STAC item collection for given region
    # 2. In parallel, extract data from STAC item collection and write to local/remote storage (this can simulataneously use multiple providers)
    # 3. Postprocess/plugins
    
    # initialize providers
    providers = [hydra.utils.instantiate(pvdr) for pvdr in cfg.providers]
    provider_item_sets = []
    
    # TODO - now, for each item...
    
    # extract STAC items for each provider; TODO this can be done in parallel
    for pvdr in providers:
        itm_set = pvdr.region_to_items(region, cfg.start_date, cfg.end_date, coll_names)
        itm_set = list(itm_set)
        logger.info(f"{pvdr} return {len(itm_set)} items for {coll_names} between {cfg.start_date} and {cfg.end_date}")

        provider_item_sets.append(itm_set)
    import ipdb; ipdb.set_trace()
    # .collection_id
    # .get_assets()
    # extract data from STAC items 
    # this can be done in parallel 
    # each item is extracted from only one provider
    
    
    
    
    
    
    

    return 0

if __name__ == "__main__":
    main()
