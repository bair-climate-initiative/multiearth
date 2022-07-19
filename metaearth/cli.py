"""CLI interface to MetaEarth."""
import argparse

from loguru import logger
from omegaconf import OmegaConf

from metaearth.api import extract_assets
from metaearth.config import ConfigSchema


def _get_args() -> argparse.Namespace:
    """Returns the parsed command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download any data from any provider with one config"
    )
    parser.add_argument("--config", type=str, help="Path to config file")
    return parser.parse_args()


if __name__ == "__main__":
    args = _get_args()
    schema = OmegaConf.structured(ConfigSchema)
    incfg = OmegaConf.load(args.config)
    cfg = OmegaConf.merge(schema, incfg)
    logger.info(f"\nUsing config: {OmegaConf.to_yaml(cfg)}")
    extract_assets(cfg)
