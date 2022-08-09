FROM registry.internal.pablintino.net/tools/builder2:v1.0.4


ARG BUILDER_INSTALLATION=/tools
ARG BUILDER_CUSTOM_CERTS=/etc/ssl/custom
ARG BUILDER_MAX_CPU_COUNT=10
ARG BUILDER_TIMEOUT_MULTIPLIER=100
ENV BUILDER_INSTALLATION $BUILDER_INSTALLATION
ENV BUILDER_CUSTOM_CERTS $BUILDER_CUSTOM_CERTS


COPY entrypoint /opt/builder2/entrypoint
COPY cpp-toolchain-metadata.json /opt/builder2/toolchain-metadata.json


RUN builder2 install -f /opt/builder2/toolchain-metadata.json  \
    -j $BUILDER_MAX_CPU_COUNT \
    -t $BUILDER_TIMEOUT_MULTIPLIER \
    -d $BUILDER_INSTALLATION

ENTRYPOINT ["/opt/builder2/entrypoint"]
CMD ["/bin/bash"]
