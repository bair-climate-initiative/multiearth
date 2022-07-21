## MetaEarth: Download any remote sensing data from any provider. 1 config.
![MetaEarth Diagram-2](https://user-images.githubusercontent.com/1455579/174143989-b04c6a22-8064-4850-897b-fe50ae7243e4.png)

---

**🔥 Warning 🔥** This is a very early alpha version of MetaEarth: things will change quickly, with little/no warning. 

---

## Quick Start

Install MetaEarth as a library and download about 18MB of [Copernicus DEM](https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-90) data from Microsoft Planetary Computer -- this small example should Just Work™ without any additional authentication.

```bash
git clone git@github.com:bair-climate-initiative/metaearth.git
cd metaearth
pip install .

# Take a look at the download using a dry run (you could also set dry_run in the config file):
python metaearth/cli.py --config config/demo.yaml system.dry_run=True

# If everything looks good, remove the dry_run and download Copernicus DEM data from Microsoft Planetary Computer
python metaearth/cli.py --config config/demo.yaml
```

**Quick Explanation:** The config we're providing, [config/demo.yaml](config/demo.yaml), contains a fully annotated example: take a look at it to get a sense of config options and how to control MetaEarth. While playing with MetaEarth, set the dryrun config option in order to display a summary of the assets without downloading anything, e.g. `system.dry_run=True`. Note that to download more/different data from Microsoft Planetary Computer, you'll want to authenticate with them (see the instructions under [Provider Configurations](#provider-configurations)).


## Documentation
**🔥 Warning 🔥** The documentation is intentionally sparse at the moment: MetaEarth is under rapid development and writing/re-updating the documentation during this period would be more effort than benefit. 

See the *Quick Start* instructions above and then consult [config/demo.yaml](config/demo.yaml) for annotated configuration (we'll keep this annotated config updated).

### Installation
```bash
# OPTIONAL: set up a conda environment (use at least python 3.7)
conda create -n metaearth python=3.8
conda activate metaearth

git clone git@github.com:bair-climate-initiative/metaearth.git
cd metaearth

# install, use -e if you want it to be in editable mode, e.g. for development
pip install -e .
```

### MetaEarth Configuration
The following describes some common goals for configuring MetaEarth, such as specifying a data collection, geographical region, and timerange to extract data from, or specifying a provider to download data from. Consult [config/demo.yaml](config/demo.yaml) for an annotated configuration. The configuration schemas are defined in [metaearth/config.py](metaearth/config.py): take a look at `ConfigSchema`. 

**Specifying the data to be downloaded** takes place through the `collections` config option. For instance, to download [Copernicus DEM](https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-90), which has the collection id `cop-dem-glo-90` (see below on how to find this), the config is like this:
```yaml
collections: 
  cop-dem-glo-90:
    # specify which assets to download. 
    # use a single entry with "all" to download all assets.
    assets:
      - data
    # the data will output to this directory.
    outdir: data/demo-extraction-dem-glo-90
    # Single date+time, or a range ('/' separator), 
    # formatted to RFC 3339, section 5.6. 
    # Use double dots .. for open date ranges.
      datetime: "2021-04-01/2021-04-23"
    # area-of-interest file location
    # this demo contains a small section in Yosemite, 
    # view by pasing demo.json into http://geojson.io
    aoi_file: config/aoi/demo.json
    provider: 
        # MPC is the identifier for Microsoft Planetary Computer
        # See "provider key" under "Provider Configurations"
        name: MPC
    
```

**Finding the collection id**: This depends on the individual provider (in the future, see [Provider Configurations](#provider-configurations) below), but for MPC, the following is a good starting point:

1. Go to the [MPC Data Catalog](https://planetarycomputer.microsoft.com/catalog)
1. Find/click-on the desired collection
1. In the Collection Overview Page, click on the "Example Notebook" tab
1. The example notebook will contain an example of accessing the collection using the collection id.

**Finding the assets**:
This depends on the individual provider (see [Provider Configurations](in the future, see #provider-configurations) below), but for MPC, the following seems to be a pretty solid method:

1. Create a config with your desired collection id, set the `assets` option to `["all"]` like this (and setting `max_items` to 1 to speed things up):
```yaml
collections: 
  landsat-8-c2-l2:
    assets:
      - all
    max_items: 1
```
1. Run a dry run to see what assets will be downloaded:
```bash
python metaearth/cli.py --config path/to/your/config.yaml system.dry_run=True
```
which will print out a list of assets that will be downloaded and their descriptions, e.g.:
```
18:24:51 INFO Asset types:
key=ANG; desc="Collection 2 Level-1 Angle Coefficients File (ANG)"
key=SR_B1; desc="Collection 2 Level-2 Coastal/Aerosol Band (B1) Surface Reflectance"
key=SR_B2; desc="Collection 2 Level-2 Blue Band (B2) Surface Reflectance"
key=SR_B3; desc="Collection 2 Level-2 Green Band (B3) Surface Reflectance"
key=SR_B4; desc="Collection 2 Level-2 Red Band (B4) Surface Reflectance"
key=SR_B5; desc="Collection 2 Level-2 Near Infrared Band 0.8 (B5) Surface Reflectance"
key=SR_B6; desc="Collection 2 Level-2 Short-wave Infrared Band 1.6 (B6) Surface Reflectance"
...
```
1. Update your config to download only the assets you want, and remove the `max_items` option:
```yaml
collections: 
  landsat-8-c2-l2:
    assets:
      - SR_B2
      - SR_B3
      - SR_B4
    max_items: 1
```

**Selecting a Region and Timerange**

**Output Format**:

**Dry run is your friend**

**DEBUG logs are also your friend. You have lots of friends.**







## Provider Configurations
Each provider needs its own authentication and setup. For each provider you'd like to use, follow the set-up instructions below.


### Microsoft Planetary Computer (provider key: MPC)

Make sure to run the following and enter your api key (this helps increase the amount of data you can download from MPC).
```
planetarycomputer configure 
```

## Contributing and Development
The general flow for development looks like this:

0. Read the Getting Started Guide - make sure you can sucessfully download some data, and make sure to install this repository in editable mode `pip install -e .`

1. Create a new branch for your feature.

2. Edit the code.

3. Run linters and tests (see subsections below)

4. Commit your changes, push to the branch, and open a pull request. 

5. ???

6. Profit $$$


### Linting
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


## Useful links

* Use https://geojson.io to extract a region-of-interest


### OmegaConf References for Config 
* [Passing in configs](https://omegaconf.readthedocs.io/en/2.2_branch/usage.html?highlight=command%20line#from-command-line-arguments)



## Related Projects

* [Sat-Extractor](https://github.com/FrontierDevelopmentLab/sat-extractor). Sat-Extractor has a similar goal as MetaEarth, though at the moment it has been designed to run on Google Compute Engine, and as of the start of MetaEarth, Sat-Extractor can only be used with Sen2 and LandSats out-of-the-box. By starting MetaEarth with Microsoft's Planetary Computer, MetaEarth immediately has access to their full data catalog: https://planetarycomputer.microsoft.com/catalog (which subsumes the data accessible by Sat-Extractor plus ~100 other sources). Still, Sat-Extractor is an awesome and highly-configurable project: please use and support it if Sat-Extractor aligns with your goals =).

