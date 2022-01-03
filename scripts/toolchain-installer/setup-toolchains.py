import json
import logging
import os

import tool_source_installer

logging.basicConfig(level=logging.DEBUG)


def __install_tools(tools_config):
    if 'components' in tools_config:
        # Mandatory field
        base_path = tools_config['base-path']

        for name, toolchain_config in tools_config['components'].items():
            with tool_source_installer.get_installer(name, toolchain_config, base_path) as installer:
                installer.run_installation()


config_file = os.environ.get('BUILDER_METADATA_PATH', '/tools/scripts/toolchain-metadata.json')
with open(config_file) as f:
    data = json.load(f)
    __install_tools(data['tools'])
