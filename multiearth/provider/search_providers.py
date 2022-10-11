# Generates list of collections that contain "snow"" in description or ID

import json
import requests
import argparse

def main(keywords) -> None:
    print("keyword(s):", keywords)
    provider_urls = ["https://planetarycomputer.microsoft.com/api/stac/v1",
    'https://cmr.earthdata.nasa.gov/stac', ]
    collection_urls = []
    for provider_url in provider_urls:
        if "earthdata" in provider_url:
            collection_hrefs = requests.get(provider_url).json()["links"]
            collection_urls += [col['href'] for col in collection_hrefs if col['rel'] == 'child']
            # print(collection_urls)
        elif "planetarycomputer" in provider_url:
            collection_urls += [provider_url]
    print(collection_urls)
    collections = []
    if keywords is None:
        return_all = True
    else:
        return_all = False
    for collection_url in collection_urls:
        response = requests.get(f'{collection_url}/collections').text

        return_collections = json.loads(response)

        for collection in return_collections["collections"]:
            collection_id = collection["id"]
            # It seems like none of the collection id's actually contain snow
            # but leaving the check here for future data sources
            keyword_exists = False
            if not return_all:
                for keyword in keywords:
                    if keyword in collection["description"] or keyword in collection["id"] or keyword in collection["title"]:
                        keyword_exists = True
                        break
            if return_all or keyword_exists:
                collections.append(collection)
                # print(collection_id)

    # with open(f"{keywords[0]}_collections.txt", 'w') as file:
    #     for collection in snow_collections:
    #         file.write("%s\n" % collection)
    #     print('Done')
    print(len(collections))
    if return_all:
        with open("all_collections.json", 'w') as file:
            json.dump(collections, file, indent=2)
    else:

        with open(f"{keywords[0]}_collections.json", 'w') as file:
            json.dump(collections, file, indent=2)
    print('Done')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search for collections')
    parser.add_argument('--keywords', nargs='+', help='Keywords to search for')
    args = parser.parse_args()
    main(args.keywords)
    exit(0)