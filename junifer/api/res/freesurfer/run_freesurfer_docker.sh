#!/bin/bash

corrected_args=()
docker_args=()
mounts=0

FS_LICENSE="${FS_LICENSE:=$HOME/freesurfer_license.txt}"

if [ -f "${FS_LICENSE}" ]; then
    >&2 echo "Using freesurfer license from ${FS_LICENSE}"
else
    >&2 echo "Freesurfer license not found at ${FS_LICENSE}. You can either set FS_LICENSE to the path of the license file or place the license file at
${FS_LICENSE}"
    exit 1
fi

# Map the license path to the container by binding
license_path=$(realpath "${FS_LICENSE}")
license_path_fname=$(basename "${FS_LICENSE}")
host_dir=$(dirname "${license_path}")
((mounts+=1))
container_dir="/data/mount_${mounts}"
docker_args+=("-v ${host_dir}:${container_dir}")
export DOCKERENV_FS_LICENSE=${container_dir}/${license_path_fname}

for var in "$@"
do
if [ -d "${var}" ]; then
        echo "$var is a directory" >&2
        var=$(realpath "${var}")
        host_dir=$(dirname "${var}")
        ((mounts+=1))
        container_dir="/data/mount_${mounts}"
        docker_args+=("-v ${host_dir}:${container_dir}")
        var=${container_dir}
    elif [ -f "${var}" ] || [[ "${var}" == /* ]]; then
        if [ -f "${var}" ]; then
            echo "$var is a file" >&2
            var=$(realpath "${var}")
        else
            echo "$var is a prefix" >&2
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

echo "Docker args: ${docker_args[*]}" >&2
echo "Corrected args for FreeSurfer: ${corrected_args[*]}" >&2

cwd=$(pwd)
cmd="docker run --rm ${docker_args[*]} -v ${cwd}:${cwd} -w ${cwd} freesurfer/freesurfer ${corrected_args[*]}"
echo "Running command: ${cmd}" >&2
${cmd}

unset DOCKERENV_FS_LICENSE
