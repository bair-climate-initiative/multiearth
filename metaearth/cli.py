"""CLI interface to MetaEarth."""
import argparse
from typing import Any, List, Tuple, cast

import omegaconf
from loguru import logger
from omegaconf import OmegaConf

from metaearth.api import extract_assets
from metaearth.config import ConfigSchema


def _get_args() -> Tuple[argparse.Namespace, List[str]]:
    """Return the parsed command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download any data from any provider with one config"
    )
    parser.add_argument("--config", type=str, help="Path to config file")
    return parser.parse_known_args()


if __name__ == "__main__":
    args, extra_args = _get_args()
    schema: ConfigSchema = OmegaConf.structured(ConfigSchema)
    incfg = OmegaConf.load(args.config)
    cfg: Any = OmegaConf.merge(schema, incfg)  # start with Any for mypy's sake

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

    use_cfg: ConfigSchema = cast(ConfigSchema, cfg)  # for mypy
    logger.info(f"\nUsing config: {OmegaConf.to_yaml(use_cfg)}")
    success = extract_assets(use_cfg)
    if cfg.system.dry_run:
        logger.info("Dry run complete.")
    else:
        logger.info(
            "All assets successfully extracted!"
            if success
            else "Some assets were not extracted -- see logs for details."
        )
