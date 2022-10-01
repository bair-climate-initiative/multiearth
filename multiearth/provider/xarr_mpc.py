"""Microsoft Planetary Computer (MPC) provider."""
from os.path import join

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import planetary_computer
import xarray as xr
from shapely.geometry import Point, Polygon
from xarray import open_zarr

from ..util.datetime import datetime_str_to_value
from .mpc import MicrosoftPlanetaryComputer


class XarrMPC(MicrosoftPlanetaryComputer):
    """Download data and extract xarray assets from MPC."""

    def get_mask(self, ds: xr.Dataset, aoi: Polygon) -> npt.NDArray[np.float64]:
        """Return a mask for resulting values that gets the area of interest."""
        mask = np.empty((len(ds.lat.values), len(ds.lon.values)))
        mask[:] = np.nan
        for i, lat in enumerate(ds.lat.values):
            for j, lon in enumerate(ds.lon.values):

                if aoi.contains(Point(lon, lat)):
                    mask[i, j] = 1
        return mask

    def extract_assets(self, dry_run: bool = False) -> bool:
        """Download a dataset to assigned output dir."""
        # TODO: use the inhereted
        catalog = self._client

        for collection in self.collections:
            assert (
                collection.datetime is not None
            ), "Collection {dataset_id} datetime is not set"
            assert (
                collection.outdir is not None
            ), "Collection {dataset_id} outdir is not set"
            assert self._client is not None, "Client not specified"
            # Try to get the dataset from MPC
            cat = catalog.get_collection(collection.id)
            assert cat is not None, "Collection not found"
            asset = planetary_computer.sign(cat.assets["zarr-abfs"])

            ds = open_zarr(
                asset.href,
                storage_options=asset.extra_fields["xarray:storage_options"],
                **asset.extra_fields["xarray:open_kwargs"],
            )

            print("collection.assets", collection.assets, type(collection.assets))
            # Select just the relevant features.

            if collection.assets is not None:
                asset_list = list(collection.assets)
                if not asset_list == ["all"]:
                    ds = ds[asset_list]

            # Select just the relevant datetime.
            if not collection.datetime == "..":
                start_date, end_date = datetime_str_to_value(collection.datetime)
                ds = ds.sel(time=slice(start_date, end_date))

            # Select just the relevant area.
            aoi = None
            if collection.aoi_file is not None:

                aoi = gpd.read_file(collection.aoi_file).unary_union
                ds = ds.loc[dict(lon=slice(aoi.bounds[0], aoi.bounds[2]))]
                # TODO: can we make this also use loc? Wasn't working for me.
                latinds = np.intersect1d(
                    np.where(ds.lat >= aoi.bounds[1]), np.where(ds.lat <= aoi.bounds[3])
                )
                ds = ds.isel(dict(lat=latinds))
                mask = self.get_mask(ds, aoi)
            else:
                mask = None

            if dry_run:
                print("dry run")
                print("dataset info")
                print(" --- ")
                print(ds.info())
                ds = ds.to_dataframe()
                print("memory usage and info")
                print(ds.info())
                print(" --- ")
            if not dry_run:
                print("beginning download")
                print("info")
                print(ds.info())
                ds.load().to_netcdf(path=join(collection.outdir, "result.nc"))
                if mask is not None:
                    np.save(join(collection.outdir, "aoi_mask.npy"), mask)

        return True
