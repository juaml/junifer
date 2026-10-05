#!/bin/bash

GH_OWNER=$GH_OWNER
GH_REPOSITORY=$GH_REPOSITORY
GH_TOKEN=$GH_TOKEN
RUNNER_SUFFIX=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 5 | head -n 1)
RUNNER_NAME="junifer-runner-${RUNNER_SUFFIX}"

dataversion=$(cat /home/docker/junifer-data-version)

cd /home/docker/actions-runner

./config.sh --url https://github.com/${GH_OWNER}/${GH_REPOSITORY} --token ${GH_TOKEN} --name ${RUNNER_NAME} --labels x64,linux,data-${dataversion}

cleanup() {
    echo "Removing runner..."
    ./config.sh remove --token ${GH_TOKEN}
}

trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

./run.sh & wait $!
