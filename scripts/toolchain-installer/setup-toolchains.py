import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import gcc_source_installer
import utils

logging.basicConfig(level=logging.DEBUG)
config_file = os.environ.get('BUILDER_METADATA_PATH', '/tools/scripts/toolchain-metadata.json')

with open(config_file) as f:
    data = json.load(f)
    base_path = Path(data['base-path'])
    base_path.mkdir(parents=True, exist_ok=True)
    for name, toolchain_config in data['toolchains'].items():
        if toolchain_config['type'] == "download-only":
            a = urlparse(toolchain_config['url'])
            file_name = os.path.basename(a.path)
            target_path = str(base_path.joinpath(Path(file_name)).resolve())
            utils.download_file(toolchain_config['url'], target_path)
            utils.extract_file(target_path, base_path)
            os.remove(target_path)
        elif toolchain_config['type'] == "gcc-build":
            gcc_source_installer.install_gcc(name, toolchain_config, base_path)
