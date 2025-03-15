#!/bin/bash

set -euo pipefail

# Local build.  See also: make remote REMOTE_HOST=mybuildhost

# This is a private image, as I'm not allowed to distribute the Xilinx ISE 14.7 files.
DOCKER_IMAGE ?= ghcr.io/myelin/xilinx_ise:v1

cd "$(dirname "$0")"
rm -rf ../cpld_tmp
cp -av . ../cpld_tmp
docker run \
    --platform=linux/amd64 \
    --rm \
    -it \
    -v $(pwd)/..:/arcflash \
    "$DOCKER_IMAGE" \
    bash -c 'cd /arcflash/cpld_tmp && make'
cp ../cpld_tmp/{*.jed,*.svf} .
