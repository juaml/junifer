#!/bin/bash

corrected_args=()
docker_args=()
mounts=0
for var in "$@"
do 
if [ -d "${var}" ]; then
        echo "$var is a directory"
        var=$(realpath "${var}")
        host_dir=$(dirname "${var}")
        ((mounts+=1))
        container_dir="/data/mount_${mounts}"
        docker_args+=("-v ${host_dir}:${container_dir}")
        var=${container_dir}
    elif [ -f "${var}" ] || [[ "${var}" == /* ]]; then
        if [ -f "${var}" ]; then
            echo "$var is a file"
            var=$(realpath "${var}")
        else
            echo "$var is a prefix"
        fi
        fname=$(basename "${var}")
        host_dir=$(dirname "${var}")
        ((mounts+=1))
        container_dir="/data/mount_${mounts}"
        docker_args+=("-v ${host_dir}:${container_dir}")
        var=${container_dir}/${fname}
    fi
    corrected_args+=("${var}")
done

echo "Docker args: ${docker_args[*]}"
echo "Corrected args for afni: ${corrected_args[*]}"

cwd=$(pwd)
cmd="docker run --rm ${docker_args[*]} -v ${cwd}:${cwd} -w ${cwd} afni/afni_make_build ${corrected_args[*]}"
echo "Running command: ${cmd}"
${cmd}