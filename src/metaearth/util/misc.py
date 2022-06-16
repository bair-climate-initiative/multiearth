import requests

# TODO this needs a lot of checking and config options
# stream file to disk without loading into memory
def download_file(url):
    local_filename = "output/demo/" + url.split('/')[-1].split('?')[0]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
    return local_filename
