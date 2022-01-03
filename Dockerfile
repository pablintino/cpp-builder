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

# Install conan and init the default profile
RUN pip3 install conan && conan config init && conan profile update settings.compiler.libcxx=libstdc++11 default

COPY scripts /tools/scripts
RUN pip3 install -r /tools/scripts/toolchain-installer/requirements.txt && python3 /tools/scripts/toolchain-installer/setup-toolchains.py

ENTRYPOINT [ "/tools/scripts/entrypoint.sh" ]
CMD ["/bin/bash"]