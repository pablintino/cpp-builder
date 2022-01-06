import json
import logging
import os
import re

__DEFAULT_SUMMARY_FILE = "/tools/scripts/.installation.json"


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
    else:
        return ""


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


def save_summary(summary):
    summary_path = os.environ.get(
        "BUILDER_INSTALLATION_SUMMARY_DIR", __DEFAULT_SUMMARY_FILE
    )
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)


def reset_summary():
    save_summary({})


def load_summary():
    config_file = os.environ.get(
        "BUILDER_INSTALLATION_SUMMARY_DIR", __DEFAULT_SUMMARY_FILE
    )
    if (
        os.path.isfile(config_file)
        and os.access(config_file, os.R_OK)
        and os.stat(config_file).st_size != 0
    ):
        with open(config_file) as f:
            try:
                return json.load(f)
            except json.decoder.JSONDecodeError:
                logging.error("Error accessing inventory file. Usually wrong format.")
    else:
        save_summary({})
        return {}


def add_tool_to_summary(tool_key, tool_metadata):
    summary = load_summary()
    if not summary:
        summary = {"tools": {"components": {}}}
    summary["tools"]["components"][tool_key] = tool_metadata
    save_summary(summary)


def __replace_non_alphanumeric_by_underscore(string):
    return re.sub("[^0-9a-zA-Z]+", "_", string) if string else string


def get_environment_definitions(summary):
    definitions = {}
    if summary and summary["tools"] and summary["tools"]["components"]:
        components = summary["tools"]["components"]
        for component_key, component_data in components.items():
            suffix_version = __component_has_multiple_versions(
                components, component_key
            )
            component_path = component_data.get("path", None)
            if component_path and (
                not suffix_version or (suffix_version and "version" in component_data)
            ):
                compiler_string = __get_compiler_triplet_from_config(component_data)
                safe_name = __replace_non_alphanumeric_by_underscore(component_key)
                if suffix_version and "version" in component_data:
                    safe_version = __replace_non_alphanumeric_by_underscore(
                        component_data["version"].strip()
                    )
                    var_name = f"BUILDER_{safe_name}_{compiler_string}_{safe_version}_DIR".upper()
                    definitions[var_name.replace("__", "_")] = component_path
                else:
                    var_name = f"BUILDER_{safe_name}_{compiler_string}_DIR".upper()
                    definitions[var_name.replace("__", "_")] = component_path

                    # If version is not mandatory is safe to add a simplified env var too based on name
                    component_name = __replace_non_alphanumeric_by_underscore(
                        component_data.get("name", None)
                    )
                    if component_name:
                        var_name = (
                            f"BUILDER_{component_name}_{compiler_string}_DIR".upper()
                        )
                        definitions[var_name.replace("__", "_")] = component_path

                    # If component is unique (no more versions or triplets) add a simple var that contains only its name
                    # Note: This applies to compilers only. Other tools already simplified by the previous variable
                    if compiler_string and __tool_has_no_alternatives(
                        components, component_key, component_data
                    ):
                        var_name = f"BUILDER_{component_name}_DIR".upper()
                        definitions[var_name.replace("__", "_")] = component_path

    return definitions
