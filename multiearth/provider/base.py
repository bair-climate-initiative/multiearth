"""Provides an abstract base class for all providers."""

import abc
from typing import Any, List

from ..config import CollectionSchema, ConfigSchema, ProviderKey


class BaseProvider(abc.ABC):
    """Abstract base class describing the provider interface."""

    id: ProviderKey
    description: str
    cfg: ConfigSchema
    collections: List[CollectionSchema]

    def __init__(
        self,
        id: ProviderKey,
        cfg: ConfigSchema,
        collections: List[CollectionSchema],
        **kwargs: Any,
    ) -> None:
        """Set up the Provider.

        It's intended that this method will be overridden by subclasses and call super().__init__().
        """
        self.id = id
        self.cfg = cfg
        self.collections = collections

        if not self.check_authorization():
            raise Exception(
                f"{self} is not authorized. See the documentation for {self}."
            )

    def __repr__(self) -> str:
        """Return a string representation of the provider."""
        desc: str = self.description if self.description else self.__class__.__name__
        return desc

    @abc.abstractmethod
    def check_authorization(self) -> bool:
        """Check if the provider is authorized - meant to be overridden."""
        return True

    @abc.abstractmethod
    def extract_assets(self, dry_run: bool = False) -> bool:
        """Extract assets from the collections in the configuration.

        Returns: True if all assets extracted successfully, False otherwise.
        """
        pass
