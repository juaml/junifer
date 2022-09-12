#!/bin/bash

if [ $# -lt 2 ]; then
    echo "This script is meant to run a command within a python environment"
    echo "It needs at least 2 parameters."
    echo "The first one must be the environment name."
    echo "The rest will be the command"
    exit 255
fi

eval "$(conda shell.bash hook)"
env_name=$1
echo "Activating ${env_name}"
conda activate "$1"
shift 1
echo "Running ${*} in virtual environment"
"$@"