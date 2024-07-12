#!/bin/bash

set -e

if [ -z "$RWD_DATA" ]; then
    echo "Environment variable RWD_DATA not defined."
    exit 1
fi

echo "Run the RWD Docker container."

set -x

docker compose up
