import json
import os
import re


__DEFAULT_SUMMARY_FILE = "/tools/scripts/.installation.json"
__DEFAULT_ENVIRONMENT_FILE = "/tools/scripts/.env"

__installation_summary__ = {}


def __replace_non_alphanumeric_by_underscore(string):
    return re.sub("[^0-9a-zA-Z]+", "_", string) if string else string


def __component_has_multiple_versions(components, component_key):
    component = None
    for _, details in components.items():
        if "name" in details and details["name"] == component_key:
            if not component:
                component = details
            elif (
                "triplet" in details
                and "triplet" in component
                and details["triplet"] == component["triplet"]
            ):
                return True
            elif "triplet" not in details and "triplet" not in component:
                return True
    return False


def __get_compiler_triplet_from_config(component_data):
    if (
        "group" in component_data
        and "compilers" == component_data["group"]
        and "triplet" in component_data
    ):
        return component_data["triplet"].strip().replace("-", "_")

    return None


def __tool_has_no_alternatives(components, component_key, component_data):
    # Name is mandatory, but as this code is part of the init script I prefer to make is 'safe' and not break
    component_name = component_data.get("name", None)
    if component_name:
        for key, details in {
            k: v for k, v in components.items() if k != component_key
        }.items():
            if "name" in details and details["name"] == component_name:
                return False
        return True
    return False


def __get_summary_path():
    summary_path = os.environ.get(
        "BUILDER_INSTALLATION_SUMMARY_PATH", __DEFAULT_SUMMARY_FILE
    )
    return summary_path if summary_path else __DEFAULT_SUMMARY_FILE


def __get_environment_file_path():
    environment_file_path = os.environ.get(
        "BUILDER_ENVIRONMENT_PATH", __DEFAULT_ENVIRONMENT_FILE
    )
    return (
        environment_file_path if environment_file_path else __DEFAULT_ENVIRONMENT_FILE
    )


def save_summary():
    global __installation_summary__
    summary_path = __get_summary_path()
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(__installation_summary__, f, indent=2)


def add_tool_to_summary(tool_key, tool_metadata):
    global __installation_summary__
    if "tools" not in __installation_summary__:
        __installation_summary__ = {"tools": {"components": {}}}
    __installation_summary__["tools"]["components"][tool_key] = tool_metadata


def get_environment_definitions():
    global __installation_summary__
    definitions = {}
    if (
        __installation_summary__
        and "tools" in __installation_summary__
        and "components" in __installation_summary__["tools"]
    ):
        components = __installation_summary__["tools"]["components"]
        for component_key, component_data in components.items():
            suffix_version = __component_has_multiple_versions(
                components, component_key
            )
            component_path = component_data.get("path", None)
            if component_path and (
                not suffix_version or (suffix_version and "version" in component_data)
            ):
                compiler_string = (
                    __get_compiler_triplet_from_config(component_data) or ""
                )
                safe_name = __replace_non_alphanumeric_by_underscore(component_key)
                if suffix_version and "version" in component_data:
                    safe_version = __replace_non_alphanumeric_by_underscore(
                        component_data["version"].strip()
                    )
                    var_name = f"BUILDER_{safe_name}_{compiler_string}_{safe_version}_DIR".upper().replace(
                        "__", "_"
                    )
                    definitions[var_name] = component_path
                else:
                    var_name = (
                        f"BUILDER_{safe_name}_{compiler_string}_DIR".upper().replace(
                            "__", "_"
                        )
                    )
                    definitions[var_name] = component_path

                    # If version is not mandatory is safe to add a simplified env var too based on name
                    component_name = __replace_non_alphanumeric_by_underscore(
                        component_data.get("name", None)
                    )
                    if component_name:
                        var_name = f"BUILDER_{component_name}_{compiler_string}_DIR".upper().replace(
                            "__", "_"
                        )
                        definitions[var_name] = component_path

                    # If component is unique (no more versions or triplets) add a simple var that contains only its name
                    # Note: This applies to compilers only. Other tools already simplified by the previous variable
                    if compiler_string and __tool_has_no_alternatives(
                        components, component_key, component_data
                    ):
                        var_name = f"BUILDER_{component_name}_DIR".upper().replace(
                            "__", "_"
                        )
                        definitions[var_name] = component_path

    return definitions


def write_environment_file():
    with open(__get_environment_file_path(), "w") as f:
        for var_name, value in get_environment_definitions().items():
            f.write(f"{var_name}={value}\n")
