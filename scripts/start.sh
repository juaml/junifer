#!/usr/bin/env bash
set -euo pipefail
: "${JITCONFIG:?JITCONFIG not set - this image must be started by the host launcher}"
cd /home/docker/actions-runner
jit="$JITCONFIG"
unset JITCONFIG
exec ./run.sh --jitconfig "$jit"