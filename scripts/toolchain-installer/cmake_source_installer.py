import logging
import os
import subprocess
import tempfile
from urllib.parse import urlparse

import utils


def __get_gcc_source_version(source_dir):
    with open(os.path.join(source_dir, 'gcc', 'BASE-VER')) as ver_file:
        return ver_file.readline().strip()


def __get_gcc_custom_build_opts(config):
    opts = config.get("config-opts", [])
    reserved = ("--target", "--host", "--build", "--enable-languages", "--prefix")
    return [x for x in opts if not x.startswith(reserved)]


def __create_gcc_options(toolchain_name, config, base_path, source_dir):
    opts = []
    if config.get("suffix-version", False):
        gcc_version = __get_gcc_source_version(source_dir)
        logging.info("GCC version read from sources: %s", gcc_version)
        suffix = f"-{gcc_version.rsplit('.', 1)[0] if gcc_version.endswith('.0') else gcc_version}"
        logging.info("GCC executables suffixed with: %s", suffix)
        opts.append(f"--program-suffix={suffix}")
    else:
        logging.info("GCC executables will not be suffixed")

    arq_guess = utils.call_process(['./config.guess'], cwd=source_dir).strip()
    logging.info("GCC config.guess result: %s", arq_guess)

    languages = ','.join(map(str, config['languages'])) if 'languages' in config else 'c,c++'
    logging.info("GCC configured languages: %s", languages)

    install_path = os.path.join(base_path, toolchain_name)
    logging.info("GCC installation path: %s", install_path)

    opts.extend([f"--build={arq_guess}",
                 f"--host={arq_guess}",
                 f"--target={arq_guess}", f"--prefix={install_path}",
                 f"--enable-languages={languages}"])
    opts.extend(__get_gcc_custom_build_opts(config))
    logging.info("GCC configure options: %s", ' '.join(map(str, opts)))
    return opts


def install_gcc(name, config, base_path):
    # File name extracted from URL
    parsed_url = urlparse(config['url'])
    with tempfile.TemporaryDirectory() as temp_build_dir:
        sources_tar_path = os.path.join(temp_build_dir, os.path.basename(parsed_url.path))
        utils.download_file(config['url'], sources_tar_path)
        source_dir = utils.extract_file(sources_tar_path, temp_build_dir)
        utils.run_process(["contrib/download_prerequisites"], cwd=source_dir, timeout=1800)

        build_path = os.path.join(temp_build_dir, 'build')
        os.mkdir(build_path)

        config_command = [os.path.join(source_dir, 'configure')]
        config_command.extend(__create_gcc_options(name, config, base_path, source_dir))
        utils.run_process(config_command, cwd=build_path, timeout=1800)

        cpu_count = os.environ.get('BUILDER_CPU_COUNT', os.cpu_count() if os.cpu_count() else 4)
        logging.info("GCC compilation CPU count %s", cpu_count)

        try:
            utils.run_process(["make", "-j", f"{cpu_count}"], cwd=build_path, timeout=7200)
            utils.run_process(["make", "install-strip"], cwd=build_path, timeout=1800)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            utils.capure_file_stdout(os.path.join(build_path, 'Makefile'))
            raise
