## MetaEarth: Download any remote sensing data from any provider using a single config.

<img width="1361" alt="MetaEarth Explainer Diagram - download any data from any provider" src="https://user-images.githubusercontent.com/1455579/180137540-80b749d0-ab3d-469d-8122-f6b1a0df008f.png">


---

**🔥 Warning 🔥** This is an early alpha version of MetaEarth: things will change quickly, with little/no warning. The current MetaEarth explainer image above is aspirational: we're actively working on adding more data providers.

---

## Quick Start

Install MetaEarth as a library and download about 18MB of [Copernicus DEM](https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-90) data from Microsoft Planetary Computer -- this small example should Just Work™ without any additional authentication.

```bash
# OPTIONAL: set up a conda environment (use at least python 3.7)
conda create -n metaearth python=3.8 geopandas
conda activate metaearth

git clone git@github.com:bair-climate-initiative/metaearth.git
cd metaearth
pip install -e . 

# Take a look at the download using a dry run (you could also set dry_run in the config file):
python metaearth/cli.py --config config/demo.yaml system.dry_run=True

# If everything looks good, remove the dry_run and download Copernicus DEM data from Microsoft Planetary Computer
python metaearth/cli.py --config config/demo.yaml

# see the extracted data in the output directory
ls data/demo-extraction-dem-glo-90/cop-dem-glo-90/
```

**Quick Explanation:** The config we're providing, [config/demo.yaml](config/demo.yaml), contains a fully annotated example: take a look at it to get a sense of config options and how to control MetaEarth. While playing with MetaEarth, set the dryrun config option in order to display a summary of the assets without downloading anything, e.g. `system.dry_run=True`. Note that to download more/different data from Microsoft Planetary Computer, you'll want to authenticate with them (see the instructions under [Provider Configurations](#provider-configurations)).


## Documentation
See the *Quick Start* instructions above and then consult [config/demo.yaml](config/demo.yaml) for annotated configuration (we'll keep this annotated config updated).


### MetaEarth Configuration
The following describes some common goals for configuring MetaEarth, such as specifying a data collection, geographical region, and timerange to extract data from, or specifying a provider to download data from. Consult [config/demo.yaml](config/demo.yaml) for an annotated configuration. The configuration schemas are defined in [metaearth/config.py](metaearth/config.py): take a look at `ConfigSchema`. 

**Specifying the data to be downloaded** takes place through the `collections` config option for each provider list in `providers`. For instance, to download [Copernicus DEM](https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-90) from Microsoft Planetary Computer (MPC), which has the collection id `cop-dem-glo-90` (see below on how to find this), the config could look like:
```yaml
providers:
  # provider id
  - id: MPC
    # collections describe the assets to extract.
    # the collection id, e.g. cop-dem-glo-90
    # is the id used to find the collection
    # in this case copernicus DEM global 90m
    # from the provider, in this case
    # Microsoft Planetary Computer
    collections:
      - id: cop-dem-glo-90
        outdir: data/demo-extraction-dem-glo-90
        # Explicitly set the assets to be downloaded or use `all` to download all assets, like this:
        # assets:
        #  - all
        assets:
          - data
```

**Finding the provider id**: see [Provider Configurations](#provider-configurations) below.

**Finding the collection id**: This depends on the individual provider (see [Provider Configurations](#Provider-Configurations) below).

**Finding the assets**:
This depends on the individual provider (see [Provider Configurations](#provider-configurations) below), but the following seems to be a pretty solid method:

1. Create a config with your desired collection id, set the `assets` option to `["all"]` like this (and setting `max_items` to 1 to speed things up):
```yaml
providers:
  - id: MPC
    collections:
        - id: landsat-8-c2-l2
          assets:
            - all 
          max_items: 1
...
```
2. Run a dry run to see what assets will be downloaded:
```bash
python metaearth/cli.py --config path/to/your/config.yaml system.dry_run=True
```
which will print out a list of assets that will be downloaded and their descriptions, e.g.:
```
To Extract:
Microsoft Planetary Computer (MPC): landsat-8-c2-l2


Collection               | Key                 | Description
--------------------------------------------------------------------------------
landsat-8-c2-l2          | ANG                 | Angle Coefficients
landsat-8-c2-l2          | SR_B1               | Coastal/Aerosol Band (B1) 
landsat-8-c2-l2          | SR_B2               | Blue Band (B2)
landsat-8-c2-l2          | SR_B3               | Green Band (B3) 
...
```
3. Let's say we want the RGB channels (see the descriptions), so we then update our config to download only the assets we want:
```yaml
  assets:
    - SR_B2
    - SR_B3
    - SR_B4
...
```

**Selecting a Region and Timerange**
Specify region:

1. Use (something like) https://geojson.io to specify the region you care about in geojson format
1. Save to file, e.g. `my_region.json`
1. Set that file to the `aoi_file` key under the collection you want to extract or to `default_collection` if you want to extract it for multiple collections.

Specify a timerange by using single date+time, or a range ('/' separator), formatted to [RFC 3339, section 5.6](https://datatracker.ietf.org/doc/html/rfc3339#section-5.6). See [config/example.yaml](config/example.yaml) and it should be pretty clear. Use double dots .. for open date ranges.


**Output Directory and Data Format**:
The saved data will be placed in the directory format `{outdir}/{collection_id}/{item_id}/{asset_id}.{asset_appendix}`. 


**Defaults when downloading multiple collections**
You can specify a `default_collection` in your config, which will be inherited by all collections that don't specify a specific key, e.g.
```yaml
# fallback for each collection
# where each of these entries can be overridden 
# in each collection config under "collections"
default_collection:

  # will output to ${output}/collection_name/ by default, can override as an entry in the collection config
  outdir: data/demo-extraction

  # default datetime range for each collection, 
  # can override as an entry in the collection config
  # Single date+time, or a range ('/' separator), 
  # formatted to RFC 3339, section 5.6. 
  # Use double dots .. for open date ranges.
  datetime: 2021-04-01/2021-04-23
  
  # default aoi for each collection (use geojson format - see geojson.io)
  # can override as an entry in the collection config
  # this demo contains a small section in Yosemite
  aoi_file: config/aoi/demo.json
  
  # Max number of items 
  # (not assets, e.g. each item could have 3 images)
  # to download. -1 for unlimited (or limit set)
  # by the provider
  max_items: -1
```

**Dry run and DEBUG are your friend. You have lots of friends.** When dialing in your configuration, keep the `system.dry_run=True` option on your call to `metaearth/cli.py` (or set it in your config). Also, set the `system.log_level=DEBUG` option to see more verbose output.

### Programmatic API Usage
Programmatic MetaEarth API usage is still under development, but very much a part of our roadmap. For now, you can roughly do the following (let us know if you're interested in API support and how you'd like to use MetaEarth in this context):

```python
from omegaconf import OmegaConf

from metaearth.api import extract_assets
from metaearth.config import ConfigSchema

dict_cfg = dict(
  providers=[
    dict(
      id="MPC",
      collections=[
        dict(
          id="cop-dem-glo-90",
          outdir="data",
          assets=["all"],
          aoi_file="config/aoi/demo.json",
          datetime="2021-04-01/2021-04-23",
        )],
    )]
)
in_cfg = OmegaConf.create(dict_cfg)
cfg_schema = OmegaConf.structured(ConfigSchema)
cfg = OmegaConf.merge(cfg_schema, in_cfg)

success = extract_assets(cfg)
print("Successfully extracted assets." if success else "Asset extraction failed.")
```


## Provider Configurations
---

**🔥 Warning 🔥** This is a very early alpha version of MetaEarth: there's only a few providers and meta-providers supported at the moment. Let us know if you need other providers and we can prioritize adding them.

---

Each provider needs its own authentication and setup. For each provider you'd like to use, follow the set-up instructions below.


### Microsoft Planetary Computer (provider key: MPC)

Make sure to run the following and enter your api key (this helps increase the amount of data you can download from MPC).
```
planetarycomputer configure 
```

**Finding the collection id**: 
1. Go to the [MPC Data Catalog](https://planetarycomputer.microsoft.com/catalog)
1. Find/click-on the desired collection
1. In the Collection Overview Page, click on the "Example Notebook" tab
1. The example notebook will contain an example of accessing the collection using the collection id.


### NASA EarthData (provider key: EARTHDATA)
NASA EarthData provides access to a diverse range of subproviders (around 60!), where each subprovider has different data sources.

**Access**
1. For NASA EarthData, you need to create an account at: https://urs.earthdata.nasa.gov/
1. Note: if using data from the ASF subprovider, you must also accept the EULA by logging into https://auth.asf.alaska.edu/
1. Add a `~/.netrc` file (if it doesn't exist) and then append the following contents:
```
machine urs.earthdata.nasa.gov
    login <username>
    password <password>
```

EarthData is a provider of providers, so you must include a `provider_id` in your `kwargs` argument to the provider, like the following example that accesses ASO data from NSIDC from EarthData ([config/nsidc.yaml](config/nsidc.yaml)):
```
collections: 
  ASO_50M_SD:
    assets:
      - data
  provider: 
    name: EARTHDATA
    kwargs:
      provider_id: NSIDC_ECS
```

**Finding the Provider ID**: Consult [earthdata_providers.py](metaearth/provider/earthdata_providers.py) for a list of providers and their provider ids.

**Finding the collection id**: TODO (this depends on the provider and we need to figure out a general approach)

### Radiant MLHub (provider key: RADIANT)
**🔥 Warning 🔥** Radiant MLHub is under development and may be rough around the edges. Let us know if you have any issues.

To query and access the data, you need to obtain an api key from [Radiant MLHub](https://mlhub.earth/). There are two ways to setup your api key with MetaEarth.

1. You can set an environment variable `MLHUB_API_KEY` as instructed by the [official documentation](https://radiant-mlhub.readthedocs.io/en/latest/authentication.html)
2. You can hardcode it as a kwarg `api_key` in the config under provider section
```yaml
providers:
  - id: RADIANT
    kwargs:
      api_key: <your_api_key>
```


See [radiant_ml_landcover.yaml](config/randiant_ml_landcover.yaml) for an example of how to configure a Radiant MLHub collection.

## Contributing and Development
The general flow for development looks like this:

0. Read the Getting Started Guide - make sure you can sucessfully download some data, and make sure to install this repository in editable mode `pip install -e .`

1. Create a new branch for your feature.

2. Edit the code.

3. Run linters and tests (see subsections below)

4. Commit your changes, push to the branch, and open a pull request. 

5. ???

6. Profit $$$


## Linting
Following [TorchGeo](https://torchgeo.readthedocs.io/en/stable/user/contributing.html#linters) (and literally copying their docs), we use the following linters:

* [black](https://black.readthedocs.io/) for code formatting
* [isort](https://pycqa.github.io/isort/) for import ordering
* [pyupgrade](https://github.com/asottile/pyupgrade) for code formatting

* [flake8](https://flake8.pycqa.org/) for code formatting
* [pydocstyle](https://www.pydocstyle.org/) for docstrings
* [mypy](https://mypy.readthedocs.io/) for static type analysis

Use [git pre-commit hooks](https://pre-commit.com/) to automatically run these checks before each commit. pre-commit is a tool that automatically runs linters locally, so that you don't have to remember to run them manually and then have your code flagged by CI. You can setup pre-commit with:

```
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Note: a small, but unexpected, oddity is that mypy runs differently as a precommit hook vs. as a standalone command (`mypy .`). Make sure both the pre-commit hook and the standalone command pass before committing.

## Testing
Data sources and providers have integration tests that are implemented via Jupyter Notebooks. Serving as both an explanatory medium and documentation, notebooks inside the `nbs` folder serve as a great way to verify that
* Required data is pulled correctly from the specified provider
* Data is able to be loaded and processed (and therefore not corrupted on download)
* A visualization is provided for users to know what their data should look like

To run notebook integration tests, follow these steps:
1. Install required test packages with `pip install -e .[tests]`
2. Execute pytest with `pytest --nbmake nbs/*`

### Addings New Tests
When writing a test notebook, please ensure you are meeting the following criteria:
1. The notebook has a simple but descriptive file name.
2. Download the smallest amount of data/assets possible to successfully run the test.
    * Avoid using `assets: all`; use `max_items: 1` instead.
    * See `nbs/grace-fo-plot.ipynb` for an example.

Your tests may require additional libraries or dependencies to load or plot the data that are not required by the main MetaEarth library. To properly execute these tests, please add your dependencies to the `setup.cfg` file under the `[options.extras_require] -> tests` section.

### Automated Test Runs and Authentication
Tests are executed automatically via [GitHub Actions](https://github.com/features/actions) when a pull request is opened against the `main` or `release` branches. You are able to verify that your PR passes tests within the PR itself.

If you are adding a new provider to MetaEarth which requires credentials in order to pull data, please work with the project maintainers to add a test username and password to the proper dotfiles and Actions Secrets for test runners to appropriately pull the data.

Adding authentication for your tests will require editing the `.github/workflows/nb_integration.yaml` file. Work with the project maintainers to achieve this.

--------

## Useful links

* Use https://geojson.io to extract a region-of-interest


### OmegaConf References for Config 
* [Passing in configs](https://omegaconf.readthedocs.io/en/2.2_branch/usage.html?highlight=command%20line#from-command-line-arguments)



## Related Projects

* [Sat-Extractor](https://github.com/FrontierDevelopmentLab/sat-extractor). Sat-Extractor has a similar goal as MetaEarth, though at the moment it has been designed to run on Google Compute Engine, and as of the start of MetaEarth, Sat-Extractor can only be used with Sen2 and LandSats out-of-the-box. By starting MetaEarth with Microsoft's Planetary Computer, MetaEarth immediately has access to their full data catalog: https://planetarycomputer.microsoft.com/catalog (which subsumes the data accessible by Sat-Extractor plus ~100 other sources). Still, Sat-Extractor is an awesome and highly-configurable project: please use and support it if Sat-Extractor aligns with your goals =).

* [openEO](https://openeo.cloud/) is a very well done project. We'll eventually add them as a provider. A key difference is that we wanted anyone to be able to add a new provider/data-source by opening a PR, rather than integrating with the openEO API.