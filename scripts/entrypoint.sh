#!/bin/sh
# vim:sw=4:ts=4:et

#!/bin/bash
# file: entrypoint.sh

set -e
export $(grep -v '^#' /tools/scripts/vars.env | xargs)
exec "$@"