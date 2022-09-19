#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

orig_val=$(md5sum "${SCRIPT_DIR}/../multiearth/provider/earthdata_providers.py")
python $SCRIPT_DIR/gen-earthdata-stac-spec.py
new_val=$(md5sum "${SCRIPT_DIR}/../multiearth/provider/earthdata_providers.py")
if [[ "$orig_val" != "$new_val" ]]; then
    echo "autogens changed for earthdata_providers.py"
    exit 1
fi

exit 0
