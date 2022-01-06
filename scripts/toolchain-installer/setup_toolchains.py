import json
import logging
import os
import sys

import installation
import tool_source_installer

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
__DEFAULT_METADATA_FILE = "/tools/scripts/toolchain-metadata.json"


def __install_tools(config):
    tools_config = config.get("tools", None)
    if tools_config and "components" in tools_config:
        # Mandatory fields: 'base-path' and 'components'
        base_path = tools_config["base-path"]
        for name, toolchain_config in tools_config["components"].items():
            with tool_source_installer.get_installer(
                name, toolchain_config, base_path
            ) as installer:
                installer.run_installation()


if __name__ == "__main__":
    installation.reset_summary()
    config_file = os.environ.get("BUILDER_METADATA_PATH", __DEFAULT_METADATA_FILE)
    with open(config_file) as f:
        __install_tools(json.load(f))
