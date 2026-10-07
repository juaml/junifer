# syntax=docker/dockerfile:1

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 LC_ALL=C.UTF-8

LABEL org.opencontainers.image.source=https://github.com/juaml/junifer \
      org.opencontainers.image.description="Junifer container image" \
      org.opencontainers.image.licenses=AGPL-3.0-only \
      BaseImage="ubuntu:24.04"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Base tooling
    ca-certificates curl git file make build-essential \
    python3 python3-venv python3-dev python-is-python3 \
    # Data
    git-annex \
    # ANTs runtime
    bc \
    # AFNI runtime (non-GUI subset of AFNI's Ubuntu 24 list)
    tcsh gsl-bin libgsl27 libglu1-mesa libglw1-mesa libxm4 libjpeg62 \
    libxmu6 libxpm4 libxi6 libxext6 libglib2.0-0t64 libgomp1 \
    netpbm xvfb xfonts-base python3-numpy python3-matplotlib r-base \
    # FSL runtime
    dc libquadmath0 \
    && rm -rf /var/lib/apt/lists/*

# --- Heavy, rarely-changing neuroimaging tools ---

# ANTs
COPY --from=antsx/ants:latest /opt/ants /opt/ants
ENV PATH="/opt/ants/bin:$PATH" \
    LD_LIBRARY_PATH="/opt/ants/lib"

# AFNI — native Ubuntu 24.04 build
RUN mkdir -p /opt/afni \
    && curl -fsSL https://afni.nimh.nih.gov/pub/dist/tgz/linux_ubuntu_24_64.tgz \
       | tar -xz -C /opt/afni --strip-components=1
ENV PATH="/opt/afni:$PATH"

# FSL
RUN curl -fsSL https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py -o /tmp/fslinstaller.py \
    && (python3 /tmp/fslinstaller.py -d /opt/fsl/ --skip_registration \
        || { cat /root/fsl_installation_*.log; exit 1; }) \
    && rm -rf /opt/fsl/pkgs /tmp/fslinstaller.py /root/fsl_installation_*.log \
    && find /opt/fsl -name '__pycache__' -prune -exec rm -rf {} +
ENV FSLDIR=/opt/fsl \
    FSLOUTPUTTYPE=NIFTI_GZ \
    PATH="/opt/fsl/share/fsl/bin:$PATH"

# --- Python environment (the system Python is externally managed) ---
RUN python3 -m venv /opt/junifer \
    && /opt/junifer/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
    && /opt/junifer/bin/pip install --no-cache-dir datalad
ENV PATH="/opt/junifer/bin:$PATH"

# --- junifer-data, version and commit taken from junifer itself ---
COPY junifer/data/utils.py /tmp/junifer_data_utils.py
RUN set -eux; \
    version="v$(sed -n 's/^JUNIFER_DATA_VERSION = "\(.*\)"/\1/p' /tmp/junifer_data_utils.py)"; \
    hexsha="$(sed -n 's/^JUNIFER_DATA_HEXSHA = "\(.*\)"/\1/p' /tmp/junifer_data_utils.py)"; \
    test "$version" != "v" && test -n "$hexsha"; \
    git config --global user.name "junifer"; \
    git config --global user.email "junifer@localhost"; \
    datalad clone https://cerebra.fz-juelich.de/junifer/junifer-data.git "$HOME/junifer_data/${version}"; \
    cd "$HOME/junifer_data/${version}"; \
    git checkout -q "${version}"; \
    test "$(git rev-parse HEAD)" = "$hexsha"; \
    datalad get -r -J 4 .; \
    test -z "$(git status --porcelain)"; \
    git log -1 --format='junifer-data %D @ %H'; \
    echo "${version}" > "$HOME/junifer-data-version"; \
    rm /tmp/junifer_data_utils.py

# --- junifer from the build context (changes most often → last) ---
# The build context must include .git so the version matches the release tag
COPY . /tmp/junifer
RUN python -m pip install --no-cache-dir "/tmp/junifer[all]" \
    && rm -rf /tmp/junifer \
    && junifer --version
