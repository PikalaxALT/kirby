#!/usr/bin/env bash

set -ueo pipefail

build_rom () {
    ROM_DIRECTORY=$(realpath $1)
    RGBDS_VERSION=$2
    shift 2
    TARGET=$@

    docker run -v ${ROM_DIRECTORY}:/rom -w /rom kemenaran/rgbds:$RGBDS_VERSION sh -c "make clean && make $TARGET"
}

build_rom resources/vanilla-rom "0.6.0" crystal11
# build_rom resources/speedchoice-rom "0.4.0"
