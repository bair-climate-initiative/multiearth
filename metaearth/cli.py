"""CLI interface to MetaEarth."""
import argparse
from typing import List, Tuple

import omegaconf
from loguru import logger
from omegaconf import OmegaConf

from metaearth.api import extract_assets
from metaearth.config import ConfigSchema


def _get_args() -> Tuple[argparse.Namespace, List[str]]:
    """Returns the parsed command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download any data from any provider with one config"
    )
    parser.add_argument("--config", type=str, help="Path to config file")
    return parser.parse_known_args()


if __name__ == "__main__":
    args, extra_args = _get_args()
    schema = OmegaConf.structured(ConfigSchema)
    incfg = OmegaConf.load(args.config)
    cfg = OmegaConf.merge(schema, incfg)
    if len(extra_args) > 0:
        cli_cfg = OmegaConf.from_cli(extra_args)
        try:
            cfg = OmegaConf.merge(cfg, cli_cfg)
        except omegaconf.errors.ValidationError as e:
            logger.error(e.msg)
            logger.error(
                "\nCLI arguments were not able to be merged with the config schema (error above)."
                + " Make sure you're using the following format "
                + "my.embedded.arg=value, e.g. system.dry_run=True"
            )

            exit(1)
    logger.info(f"\nUsing config: {OmegaConf.to_yaml(cfg)}")
    extract_assets(cfg)
