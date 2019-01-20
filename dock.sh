#!/bin/sh

# Builds pypng distribution and documentation files.
# Using docker.

set -e
set -u

cd ${PWD%pypng*}pypng
printf 1>&2 "Running in directory $PWD\n"

. ./pypng-version
docker build -t pypng-build -f build.Dockerfile .
mkdir -p dist

run () {
  docker run --mount type=bind,source=$PWD,destination=/pypng "$@"
}

run pypng-build sh -c 'sphinx-build -N -d sphinx-crud -a man html'
run pypng-build sh -c 'python setup.py sdist'
run --workdir /pypng/html pypng-build /usr/bin/zip -r - . > dist/pypng-$PYPNG_VERSION-doc.zip
