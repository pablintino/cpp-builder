FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y \
    apt-utils \
    curl \
    wget \
    automake \
    autogen \
    bash \
    bc \
    ca-certificates \
    curl \
    cmake \
    file \
    git \
    make \
    ncurses-dev \
    pkg-config \
    libtool \
    python3 \
    python3-pip \
    ninja-build \
    sed \
    bison \
    flex \
    tar \
    bzip2 \
    gzip \
    runit \
    xz-utils \
    libssl-dev

ARG BUILDER_METADATA_PATH
ARG BUILDER_ENVIRONMENT_PATH=/tools/scripts/.env
ARG BUILDER_INSTALLATION_SUMMARY_PATH
ARG BUILDER_CONAN_PROFILES_PATH
ARG BUILDER_MAX_CPU_COUNT
ARG BUILDER_TIMEOUT_MULTIPLIER
ENV BUILDER_ENVIRONMENT_PATH $BUILDER_ENVIRONMENT_PATH

# Install conan and init the default profile
RUN pip3 install conan && conan config init && conan profile update settings.compiler.libcxx=libstdc++11 default

COPY scripts /tools/scripts
ENV PATH="/tools/scripts:${PATH}"
RUN pip3 install -r /tools/scripts/toolchain-installer/requirements.txt && python3 /tools/scripts/toolchain-installer/setup_toolchains.py

ENTRYPOINT ["/tools/scripts/entrypoint"]
CMD ["/bin/bash"]