import argparse
import asyncio
import os
import sys
from datetime import date
from typing import Any, Dict, List

import geopandas as gpd
from loguru import logger
from omegaconf import OmegaConf
from tqdm.asyncio import tqdm

from metaearth.config import ConfigSchema
from metaearth.api import extract_assets

def get_args() -> argparse.Namespace:
    """Returns the parsed command line arguments"""
    parser = argparse.ArgumentParser(description="Download any data from any provider with one config")
    parser.add_argument("--config", type=str, help="Path to config file")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    schema = OmegaConf.structured(ConfigSchema)
    incfg = OmegaConf.load(args.config)
    cfg = OmegaConf.merge(schema, incfg)
    logger.info(f"\nUsing config: {OmegaConf.to_yaml(cfg)}")
    asyncio.run(extract_assets(cfg))
