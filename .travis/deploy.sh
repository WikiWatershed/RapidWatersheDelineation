#!/usr/bin/env bash

set -e

if [ -z "${TRAVIS_TAG}" ]; then
  QUAY_TAG="${TRAVIS_COMMIT:0:7}"
else
  QUAY_TAG="${TRAVIS_TAG}"

  docker tag "quay.io/wikiwatershed/rwd:${TRAVIS_COMMIT:0:7}" "quay.io/wikiwatershed/rwd:${QUAY_TAG}"
fi

docker push "quay.io/wikiwatershed/rwd:${QUAY_TAG}"
docker tag  "quay.io/wikiwatershed/rwd:${QUAY_TAG}" "quay.io/wikiwatershed/rwd:latest"
docker push "quay.io/wikiwatershed/rwd:latest"
