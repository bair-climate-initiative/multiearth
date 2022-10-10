# Generates list of collections that contain "snow" in description or ID

import json
import requests


def main() -> None:
    api_url = "https://planetarycomputer.microsoft.com/api/stac/v1/collections"

    response = requests.get(api_url).text

    collections = json.loads(response)

    snow_collections = []

    for collection in collections["collections"]:
        collection_id = collection["id"]
        # It seems like none of the collection id's actually contain snow
        # but leaving the check here for future data sources
        if "snow" in collection["description"] or "snow" in collection["id"]:
            snow_collections.append(collection)
            print(collection_id)

    with open("snow_collections.txt", 'w') as file:
        for collection in snow_collections:
            file.write("%s\n" % collection)
        print('Done')


if __name__ == "__main__":
    main()
    exit(0)
