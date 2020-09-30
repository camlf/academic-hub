#!/bin/bash

set -e
pushd /srv/deschutes
python -m http.server 8000 &
popd

# python -m nbviewer --port=8080 --base-url=/nbviewer/
exec "$@" 
