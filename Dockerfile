FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y \
    apt-utils \
    curl \
    wget \
    automake \
    autogen \
    bash \
    bc \
    bzip2 \
    ca-certificates \
    curl \
    file \
    git \
    gzip \
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
    runit \
    xz-utils \
    libssl-dev

# Install a recent copy of cmake
RUN  wget -c  https://github.com/Kitware/CMake/releases/download/v3.22.1/cmake-3.22.1.tar.gz -O - | \
    tar -xz -C /tmp && \
    cd /tmp/cmake-3.22.1 && \
    ./bootstrap && \
    make && \
    make install && \
    rm -rf /tmp/cmake-3.22.1

# Install conan and init the default profile
RUN pip3 install conan && \
    conan config init && \
    conan profile update settings.compiler.libcxx=libstdc++11 default

# Install cross-compilation toolchains
WORKDIR "/tools/scripts"
COPY scripts /tools/scripts
RUN pip3 install -r requirements.txt && python3 setup-toolchains.py

# -c to allow commands to be passed as a string argument that can have placeholders
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
