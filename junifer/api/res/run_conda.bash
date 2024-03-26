#!/usr/bin/env bash

if [ $# -lt 2 ]; then
    echo "This script is meant to run a command within a conda environment."
    echo "It needs at least 2 parameters."
    echo "The first one must be the environment name."
    echo "The rest will be the command."
    exit 255
fi

eval "$(conda shell.bash hook)"
env_name=$1
echo "Activating ${env_name}"
conda activate "${env_name}"
shift 1

if [ -f "pre_run.sh" ]; then
    echo "Sourcing pre_run.sh"
    . ./pre_run.sh
fi

echo "Running ${*} in conda environment"
"$@"
