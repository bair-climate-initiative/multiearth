# MetaEarth
![MetaEarth Diagram-2](https://user-images.githubusercontent.com/1455579/174143989-b04c6a22-8064-4850-897b-fe50ae7243e4.png)
Download remote sensing data from any provider through a single config.

**Warning:** This is a very early alpha version of MetaEarth: things will change quickly, with little/no warning. Right now, there is no pip/conda-installable version of MetaEarth (you must git clone this repo).

## Installation
```bash
git clone git@github.com:bair-climate-initiative/metaearth.git
cd metaearth

# OPTIONAL: set up a conda environment (use at least python 3.7)
conda create -n metaearth python=3.8
conda activate metaearth

# install
pip install -e .
```


## Development

### Linting
Similar to [TorchGeo](https://torchgeo.readthedocs.io/en/stable/user/contributing.html#linters), we use the following linters:

* `[black](https://black.readthedocs.io/) for code formatting
* `[isort](https://pycqa.github.io/isort/) for import ordering
* `[pyupgrade](https://github.com/asottile/pyupgrade) for code formatting

* `[flake8](https://flake8.pycqa.org/) for code formatting
* `[pydocstyle](https://www.pydocstyle.org/) for docstrings
* `[mypy](https://mypy.readthedocs.io/) for static type analysis

> You can also use `git pre-commit hooks <https://pre-commit.com/>`_ to automatically run these checks before each commit. pre-commit is a tool that automatically runs linters locally, so that you don't have to remember to run them manually and then have your code flagged by CI. You can setup pre-commit with:

.. code-block:: console

   $ pip install pre-commit
   $ pre-commit install
   $ pre-commit run --all-files

## Quick Tutorial (5 minutes)

## Configuration
MetaEarth uses a single configuration format to acquire data from any data provider.

<!-- TODO: discuss when to use more than one config file for a set of imagery -->

## Provider Configurations f
Each provider needs its own authentication and setup. For each provider you'd like to use, follow the set-up instructions below.

### Microsoft Planetary Computer

Make sure to run the following and enter your api key (this helps increase the amount of data you can download from MPC).
```
planetarycomputer configure 
```



## Development
```
pip install -e .
```

## Related Projects

* [Sat-Extractor](https://github.com/FrontierDevelopmentLab/sat-extractor#authentication). Sat-Extractor has the same goal as MetaEarth, though at the moment it has been designed to run on Google Compute Engine and this project required a number of changes. Much of the structure and code (and permissive license!) from this project comes from Sat-Extractor.

## Useful links

* Use https://geojson.io to extract a region-of-interest    



### OmegaConf References for Config 
* [Passing in configs](https://omegaconf.readthedocs.io/en/2.2_branch/usage.html?highlight=command%20line#from-command-line-arguments)

