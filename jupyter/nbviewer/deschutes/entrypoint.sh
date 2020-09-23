#!/bin/bash
set -e

pushd /srv/deschutes
python -m http.server 8000 &
popd

exec "$@" 
