#!/bin/bash

corrected_args=()
docker_args=()
mounts=0
for var in "$@"
do
    if [ -f "${var}" ]; then
        echo "$var is a file"
        var=$(realpath "${var}")
        fname=$(basename "${var}")
        host_dir=$(dirname "${var}")
        mounts+=1
        container_dir="/data/mount_${mounts}"
        docker_args+=("-v ${host_dir}:${container_dir}")
        var=${container_dir}/${fname}
    elif [ -d "${var}" ]; then
        echo "$var is a directory"
        var=$(realpath "${var}")
        host_dir=$(dirname "${var}")
        mounts+=1
        container_dir="/data/mount_${mounts}"
        docker_args+=("-v ${host_dir}:${container_dir}")
        var=${container_dir}
    fi
    corrected_args+=("${var}")
done

echo "Docker args: ${docker_args[*]}"
echo "Corrected args for afni: ${corrected_args[*]}"

cwd=$(pwd)
cmd="docker run --rm -ti ${docker_args[*]} -v ${cwd}:${cwd} -w ${cwd} afni/afni_make_build ${corrected_args[*]}"
${cmd}