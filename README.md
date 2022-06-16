# MetaEarth

![MetaEarth Diagram-2](https://user-images.githubusercontent.com/1455579/174143989-b04c6a22-8064-4850-897b-fe50ae7243e4.png)
Download remote sensing data from any provider through a single config.


## Provider Configurations

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



