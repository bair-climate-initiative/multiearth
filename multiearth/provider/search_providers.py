"""Generates list of collections that contain "snow"" in description or ID."""

import argparse
import json
from collections import defaultdict
from typing import DefaultDict, List, Optional

import requests


def main(keywords: Optional[List[str]]) -> None:
    """Save collections given keywords. If no keywords are given, save all collections."""
    print("keyword(s):", keywords)
    provider_urls = [
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        "https://cmr.earthdata.nasa.gov/stac",
    ]
    collection_urls = []
    for provider_url in provider_urls:
        if "earthdata" in provider_url:
            collection_hrefs = requests.get(provider_url).json()["links"]
            collection_urls += [
                col["href"] for col in collection_hrefs if col["rel"] == "child"
            ]
        elif "planetarycomputer" in provider_url:
            collection_urls += [provider_url]
    collections = []
    # if keywords is None:
    #     return_all = True
    # else:
    #     return_all = False
    for collection_url in collection_urls:
        response = requests.get(f"{collection_url}/collections").text

        return_collections = json.loads(response)

        for collection in return_collections["collections"]:
            keyword_exists = False
            if keywords is not None:
                for keyword in keywords:
                    if (
                        keyword in collection["description"]
                        or keyword in collection["id"]
                        or keyword in collection["title"]
                    ):
                        keyword_exists = True
                        break
            if (keywords is None) or keyword_exists:
                collections.append(collection)

    print("Number of collections:", len(collections))
    if keywords is None:
        with open("all_collections.json", "w") as file:
            json.dump(collections, file, indent=2)
        grouped_collections = defaultdict(list)
        for collection in collections:
            title = collection["title"][0]
            grouped_collections[title].append(collection)
        for value in grouped_collections.values():
            value.sort(key=lambda x: x["title"])
        with open("all_collections_alphabetical.json", "w") as file:
            json.dump(grouped_collections, file, indent=2)
    else:
        with open(f"{keywords[0]}_collections.json", "w") as file:
            json.dump(collections, file, indent=2)
    print("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for collections")
    parser.add_argument("--keywords", nargs="+", help="Keywords to search for")
    args = parser.parse_args()
    main(args.keywords)
    exit(0)
