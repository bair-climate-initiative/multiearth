"""API for downloading assets programmatically. Use cli.py to download assets from command line."""

import datetime
import os
import sys
from typing import Any, List, cast

from loguru import logger
from omegaconf import OmegaConf

from .config import CollectionSchema, ConfigSchema
from .provider import get_provider
from .provider.base import BaseProvider


def extract_assets(cfg: ConfigSchema) -> bool:
    """Run the full MetaEarth asset extraction process.

    Args:
        cfg: a dict config object
    Returns:
        True if all assets were extracted successfully, False otherwise
    """
    # date and time string to identify the run
    collection_names = [
        cltn.id for pvdr in cfg.providers for cltn in pvdr.collections if cltn.id
    ]
    cfg.run_id = (
        f"{'-'.join(sorted(collection_names))}_{datetime.datetime.now():%Y-%m-%d-%H:%m}"
    )

    _setup_logger(cfg)
    pvdrs = _initialize_providers(cfg)

    # TODO paralellize this (not sure how the logging would look though)
    all_succeed = True
    for pvdr in pvdrs:
        all_succeed &= pvdr.extract_assets(dry_run=cfg.system.dry_run)
    return all_succeed


def _initialize_providers(cfg: ConfigSchema) -> List[BaseProvider]:
    """Initialize all of the providers with the collections they'll extract."""
    pvdrs: List[BaseProvider] = []
    # for each provider, obtain the config for the collections it will extract (merge with default)
    # then initialize the provider
    for pvdr_cfg in cfg.providers:
        new_collections = []
        for collection in pvdr_cfg.collections:
            assert (
                collection.id is not None
            ), f"Collection {collection} must provide an id."
            non_empty_cfg = {
                k: val for k, val in collection.items() if val and val != -1  # type: ignore
            }
            newcfg: Any = OmegaConf.merge(cfg.default_collection, non_empty_cfg)
            newcfg = cast(CollectionSchema, newcfg)
            new_collections.append(newcfg)
            logger.info(
                f"Extraction details for provider {pvdr_cfg.id} with collection "
                + f"{collection.id}: \n{OmegaConf.to_yaml(pvdr_cfg.collections[-1])}"
            )
        pvdr_cfg.collections = new_collections
        pvdr = get_provider(pvdr_cfg.id, cfg, pvdr_cfg.collections, **pvdr_cfg.kwargs)
        pvdrs.append(pvdr)
    return pvdrs


def _setup_logger(cfg: ConfigSchema) -> None:
    """Set up the logger."""
    # string to identify the run

    # create output log dir if not exists
    if not os.path.exists(cfg.system.log_outdir):
        os.makedirs(cfg.system.log_outdir)

    # set logging level and log output
    logger.remove()
    # TODO different log levels should have different colors
    logger.add(
        sys.stderr,
        format="<blue>{time:HH:mm:ss}</blue> <yellow>{level}</yellow> - <bold>{message}</bold>",
        level=cfg.system.log_level,
        colorize=True,
    )
    log_output_file = os.path.join(cfg.system.log_outdir, f"{cfg.run_id}.log")
    logger.add(
        log_output_file,
        format="{time:HH:mm:ss} {level} {message}",
        level=cfg.system.log_level,
    )

    # write the config to file
    yaml_cfg = OmegaConf.to_yaml(cfg)
    with open(os.path.join(cfg.system.log_outdir, f"{cfg.run_id}_cfg.yaml"), "w") as f:
        f.write(str(yaml_cfg))
