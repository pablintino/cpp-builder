import logging
import os
import pathlib
import subprocess

import utils
import tempfile
from urllib.parse import urlparse


class ToolSourceInstaller:

    def __init__(self, tool_name, config, base_install_dir):
        self.tool_name = tool_name
        self._config = config
        self._url = config['url']
        self._target_dir = os.path.join(base_install_dir, tool_name)

        # If tool is in a group install in their directory
        if 'group' in config and config['group']:
            self._target_dir = os.path.join(base_install_dir, config['group'], tool_name)
        else:
            self._target_dir = os.path.join(base_install_dir, tool_name)

        if not os.path.exists(self._target_dir):
            pathlib.Path(self._target_dir).mkdir(parents=True, exist_ok=True)

        self._temp_dir = None
        self._sources_dir = None

    def __enter__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, type, value, traceback):
        self._temp_dir.cleanup()

    def _acquire_sources(self):
        parsed_url = urlparse(self._url)
        sources_tar_path = os.path.join(self._temp_dir.name, os.path.basename(parsed_url.path))
        utils.download_file(self._url, sources_tar_path)
        self._sources_dir = utils.extract_file(sources_tar_path, self._temp_dir.name)

    def _create_config_cmd(self):
        return [os.path.join(self._sources_dir, 'configure')]

    def _create_build_cmd(self):
        return ['make']

    def _create_install_cmd(self):
        return ['make', 'install']

    def _configure(self, timeout=300, directory=None):
        utils.run_process(self._create_config_cmd(), cwd=self._sources_dir if not directory else directory,
                          timeout=timeout)

    def _build(self, timeout=3600, directory=None):
        utils.run_process(self._create_build_cmd(), cwd=self._sources_dir if not directory else directory,
                          timeout=timeout)

    def _install(self, timeout=3600, directory=None):
        utils.run_process(self._create_install_cmd(), cwd=self._sources_dir if not directory else directory,
                          timeout=timeout)

    def run_installation(self):
        self._acquire_sources()
        self._configure()
        self._build()
        self._install()


class CMakeSourcesInstaller(ToolSourceInstaller):
    def _create_config_cmd(self):
        cpu_count = os.environ.get('BUILDER_CPU_COUNT', os.cpu_count() if os.cpu_count() else 4)
        logging.info("CMake compilation CPU count %s", cpu_count)
        return [os.path.join(self._sources_dir, 'bootstrap'), f"--parallel={cpu_count}", f"--prefix={self._target_dir}"]


class GccSourcesInstaller(ToolSourceInstaller):

    def __get_gcc_source_version(self):
        with open(os.path.join(self._sources_dir, 'gcc', 'BASE-VER')) as ver_file:
            return ver_file.readline().strip()

    def __get_gcc_custom_build_opts(self):
        opts = self._config.get("config-opts", [])
        reserved = ("--target", "--host", "--build", "--enable-languages", "--prefix")
        return [x for x in opts if not x.startswith(reserved)]

    def _create_config_cmd(self):
        opts = []
        if self._config.get("suffix-version", False):
            gcc_version = self.__get_gcc_source_version()
            logging.info("GCC version read from sources: %s", gcc_version)
            suffix = f"-{gcc_version.rsplit('.', 1)[0] if gcc_version.endswith('.0') else gcc_version}"
            logging.info("GCC executables suffixed with: %s", suffix)
            opts.append(f"--program-suffix={suffix}")
        else:
            logging.info("GCC executables will not be suffixed")

        arq_guess = utils.call_process(['./config.guess'], cwd=self._sources_dir).strip()
        logging.info("GCC config.guess result: %s", arq_guess)

        languages = ','.join(map(str, self._config['languages'])) if 'languages' in self._config else 'c,c++'
        logging.info("GCC configured languages: %s", languages)

        logging.info("GCC installation path: %s", self._target_dir)

        opts.extend([f"--build={arq_guess}",
                     f"--host={arq_guess}",
                     f"--target={arq_guess}", f"--prefix={self._target_dir}",
                     f"--enable-languages={languages}"])
        opts.extend(self.__get_gcc_custom_build_opts())
        logging.info("GCC configure options: %s", ' '.join(map(str, opts)))

        command = [os.path.join(self._sources_dir, 'configure')]
        command.extend(opts)
        return command

    def _create_build_cmd(self):
        cpu_count = os.environ.get('BUILDER_CPU_COUNT', os.cpu_count() if os.cpu_count() else 4)
        logging.info("GCC compilation CPU count %s", cpu_count)
        return ['make', "-j", f"{cpu_count}"]

    def _create_install_cmd(self):
        return ['make', 'install-strip']

    def run_installation(self):
        self._acquire_sources()

        # Download required libs before start configuration
        utils.run_process(["contrib/download_prerequisites"], cwd=self._sources_dir, timeout=1800)

        build_path = os.path.join(self._temp_dir.name, 'build')
        os.mkdir(build_path)

        self._configure(directory=build_path, timeout=1800)
        try:
            self._build(directory=build_path, timeout=7200)
            self._install(directory=build_path, timeout=1800)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            #utils.capure_file_stdout(os.path.join(build_path, 'Makefile'))
            raise


def get_installer(tool_name, config, base_install_dir):
    installer_type = config['type']
    if installer_type == 'gcc-build':
        return GccSourcesInstaller(tool_name, config, base_install_dir)
    if installer_type == 'cmake-build':
        return CMakeSourcesInstaller(tool_name, config, base_install_dir)

    raise SystemExit(f'Installer type not supported {installer_type}')
