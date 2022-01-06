#!/usr/bin/python3

import os
import subprocess
import sys
import installation


def __add_component_env_vars(json_data):
    for name, value in installation.get_environment_definitions(json_data).items():
        os.environ[name] = value


def __run_exec():
    args = sys.argv[1:]

    command = f"/bin/bash -l -c \"{' '.join(map(str, args))}\"" if args else "/bin/bash"
    result = subprocess.run(command, shell=True)
    sys.exit(result.returncode)


if __name__ == "__main__":
    # Protection to avoid possible shell recursion
    if os.getenv("BUILDER_INSIDE_SHELL", "False").lower() in ("true", "1"):
        raise SystemExit("Error: Cannot nest cpp-builder sessions")
    os.environ["BUILDER_INSIDE_SHELL"] = str(True)

    __add_component_env_vars(installation.load_summary())
    __run_exec()
