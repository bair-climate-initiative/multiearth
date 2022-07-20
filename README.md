# MetaEarth
![MetaEarth Diagram-2](https://user-images.githubusercontent.com/1455579/174143989-b04c6a22-8064-4850-897b-fe50ae7243e4.png)
*Download any remote sensing data from any provider using a single config.*

---
---

**🔥 Warning 🔥** This is a very early alpha version of MetaEarth: things will change quickly, with little/no warning. 

---
---

## Quick Start

Install MetaEarth as a library and download about 20MB of [Copernicus DEM](https://planetarycomputer.microsoft.com/dataset/cop-dem-glo-90) data from Microsoft Planetary Computer -- this small example should Just Work™ without any additional authentication.

```bash
git clone git@github.com:bair-climate-initiative/metaearth.git
cd metaearth
pip install .

# Take a look at the download using a dry run (you could also set dry_run in the config file):
python metaearth/cli.py --config config/demo.yaml system.dry_run=True

# If everything looks good, remove the dry_run and download Copernicus DEM data from Microsoft Planetary Computer
python metaearth/cli.py --config config/demo.yaml
```

**Quick Explanation:** The config we're providing, [config/demo.yaml](config/demo.yaml), contains a fully annotated example: take a look at it to get a sense of config options and how to control MetaEarth. While playing with MetaEarth, set the dryrun config option in order to display a summary of the assets without downloading anything, e.g. `system.dry_run=True` 


## Documentation
**🔥 Warning 🔥** The documentation is intentionally sparse at the moment: MetaEarth is under rapid development and writing/re-updating the documentation for during this period would be more effort than benefit. 

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

### Configuring MetaEarth
Consult [config/demo.yaml](config/demo.yaml) for an annotated configuration. The configuration schemas are defined in [metaearth/config.py](metaearth/config.py): take a look at `ConfigSchema`.


## Provider Configurations
Each provider needs its own authentication and setup. For each provider you'd like to use, follow the set-up instructions below.

### Microsoft Planetary Computer

Make sure to run the following and enter your api key (this helps increase the amount of data you can download from MPC).
```
planetarycomputer configure 
```

## Related Projects

* [Sat-Extractor](https://github.com/FrontierDevelopmentLab/sat-extractor). Sat-Extractor has a similar goal as MetaEarth, though at the moment it has been designed to run on Google Compute Engine, and as of the start of MetaEarth, Sat-Extractor can only be used with Sen2 and LandSats out-of-the-box. By starting MetaEarth with Microsoft's Planetary Computer, MetaEarth immediately has access to their full data catalog: https://planetarycomputer.microsoft.com/catalog (which subsumes the data accessible by Sat-Extractor plus ~100 other sources). Still, Sat-Extractor is an awesome and highly-configurable project: please use and support it if Sat-Extractor aligns with your goals =).


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

> Use `git pre-commit hooks <https://pre-commit.com/>`_ to automatically run these checks before each commit. pre-commit is a tool that automatically runs linters locally, so that you don't have to remember to run them manually and then have your code flagged by CI. You can setup pre-commit with:

```
pip install pre-commit
pre-commit install
pre-commit run --all-files
```


## Useful links

* Use https://geojson.io to extract a region-of-interest


### OmegaConf References for Config 
* [Passing in configs](https://omegaconf.readthedocs.io/en/2.2_branch/usage.html?highlight=command%20line#from-command-line-arguments)

