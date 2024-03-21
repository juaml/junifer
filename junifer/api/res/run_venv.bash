#!/usr/bin/env bash

if [ $# -lt 2 ]; then
    echo "This script is meant to run a command within a Python virtual environment."
    echo "It needs at least 2 parameters."
    echo "The first one must be the virtualenv path."
    echo "The rest will be the command."
    exit 255
fi

env_path=$1
echo "Activating ${env_path}"
source "${env_path}"/bin/activate
shift 1

if [ -f "pre_run.sh" ]; then
    echo "Sourcing pre_run.sh"
    . ./pre_run.sh
fi

echo "Running ${*} in Python virtual environment"
"$@"
