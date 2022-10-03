"""Microsoft Planetary Computer (MPC) provider."""
from os.path import join

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import planetary_computer
import pyproj
import xarray as xr
from shapely.geometry import Point, Polygon
from shapely.ops import transform
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

    def get_xf_aoi(self, ds: xr.Dataset, aoi: Polygon) -> Polygon:
        """Transform a mask into the dataset's lambert canonical coordinate projection."""
        lcc = ds.variables["lambert_conformal_conic"].attrs
        prj_kwargs = dict(
            central_latitude=lcc["latitude_of_projection_origin"],
            central_longitude=lcc["longitude_of_central_meridian"],
            standard_parallels=(lcc["standard_parallel"]),
        )
        lon0 = prj_kwargs["central_longitude"]
        lat0 = prj_kwargs["central_latitude"]
        lat1 = prj_kwargs["standard_parallels"][0]
        lat2 = prj_kwargs["standard_parallels"][1]
        lambstr = f"+proj=lcc +lat_0={lat0} +lon_0={lon0} +lat_1={lat1} +lat_2={lat2}"
        lambstr += "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        project = pyproj.Transformer.from_proj(
            pyproj.Proj(init="epsg:4326"), pyproj.Proj(lambstr)
        )
        aoi_xf = transform(project.transform, aoi)
        return aoi_xf

    def get_mask_proj(self, ds: xr.Dataset, aoi_xf: Polygon) -> npt.NDArray[np.float64]:
        """Get mask for projection rather than lat/lon."""
        mask = np.empty((len(ds.x.values), len(ds.y.values)))
        mask[:] = np.nan
        for i, x in enumerate(ds.x.values):
            for j, y in enumerate(ds.y.values):
                if aoi_xf.contains(Point(x, y)):
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
            # Select just the relevant features.

            if collection.assets is not None:
                asset_list = list(collection.assets)
                if not asset_list == ["all"]:

                    if len(ds.lat.shape) == 2:
                        assert (
                            "lambert_conformal_conic" in ds.variables
                        ), "Only lambert conformal conic projections are currently supported"
                        ds = ds[asset_list + ["lambert_conformal_conic"]]
                    else:
                        ds = ds[asset_list]

            # Select just the relevant datetime.
            if not collection.datetime == "..":
                start_date, end_date = datetime_str_to_value(collection.datetime)
                ds = ds.sel(time=slice(start_date, end_date))

            # Select just the relevant area.
            aoi = None
            if collection.aoi_file is not None:
                aoi = gpd.read_file(collection.aoi_file).unary_union

                if len(ds.lat.shape) < 2:
                    # Data is not projected, use lat and long to get mask and subselect data
                    ds = ds.loc[dict(lon=slice(aoi.bounds[0], aoi.bounds[2]))]
                    # TODO: can we make this also use loc? Wasn't working for me.
                    latinds = np.intersect1d(
                        np.where(ds.lat >= aoi.bounds[1]),
                        np.where(ds.lat <= aoi.bounds[3]),
                    )
                    ds = ds.isel(dict(lat=latinds))
                    mask = self.get_mask(ds, aoi)

                elif len(ds.lat.shape) == 2:
                    aoi_xf = self.get_xf_aoi(ds, aoi)
                    ds = ds.loc[dict(x=slice(aoi_xf.bounds[0], aoi_xf.bounds[2]))]
                    latinds = np.intersect1d(
                        np.where(ds.y >= aoi_xf.bounds[1]),
                        np.where(ds.y <= aoi_xf.bounds[3]),
                    )
                    ds = ds.isel(dict(y=latinds))
                    mask = self.get_mask_proj(ds, aoi_xf)
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
                ds.load().to_netcdf(
                    path=join(collection.outdir, f"{collection.id}_result.nc"), mode="w"
                )
                if mask is not None:
                    np.save(
                        join(collection.outdir, f"{collection.id}_aoi_mask.npy"), mask
                    )

        return True
