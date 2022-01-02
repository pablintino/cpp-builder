import io
import logging
import os
import subprocess
import tarfile

import requests
from tqdm import tqdm


class ProgressFileObject(io.FileIO):
    def __init__(self, path, *args, **kwargs):
        self._total_size = os.path.getsize(path)
        self.__count = 0
        self.__tqdm = tqdm(total=self._total_size, unit='iB', unit_scale=True, unit_divisor=1024)
        io.FileIO.__init__(self, path, *args, **kwargs)

    def read(self, size):
        pos = self.tell()
        if self.__count != pos:
            self.__tqdm.update(pos - self.__count)
        self.__count = pos
        return io.FileIO.read(self, size)

    def close(self):
        super(ProgressFileObject, self).close()
        self.__tqdm.close()


def download_file(url, fname):
    logging.info("Start download of %s", url)
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    with open(fname, 'wb') as file, tqdm(
            desc=fname,
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


def extract_file(file, target):
    logging.info("Start extraction of %s", file)
    with tarfile.open(fileobj=ProgressFileObject(file)) as tar:
        tar.extractall(target)
        return os.path.join(target, os.path.commonprefix(tar.getnames()))


def call_process(arg_list, cwd=None, timeout=180):
    command_str = ' '.join(map(str, arg_list))
    working_dir = os.getcwd() if not cwd else cwd
    logging.info("Call command: %s", command_str)
    try:
        return subprocess.check_output(arg_list, stdin=subprocess.DEVNULL, universal_newlines=True, cwd=working_dir,
                                       timeout=timeout)
    except subprocess.CalledProcessError:
        logging.error("Failed to execute [%s]. Timeout (%d)", command_str, timeout)
        raise
    except subprocess.TimeoutExpired:
        logging.error("Failed to execute [%s]. Timeout (%d)", command_str, timeout)
        raise


def run_process(arg_list, cwd=None, timeout=180):
    command_str = ' '.join(map(str, arg_list))
    logging.info("Run command: %s", command_str)
    working_dir = os.getcwd() if not cwd else cwd
    try:
        subprocess.run(arg_list, cwd=working_dir, timeout=timeout, check=True)
    except subprocess.CalledProcessError:
        logging.error("Failed to execute [%s]. Exit code non-zero.", command_str)
        raise
    except subprocess.TimeoutExpired:
        logging.error("Failed to execute [%s]. Timeout (%d)", command_str, timeout)
        raise


def capure_file_stdout(path):
    print("##################### START OF FILE OUTPUT ##################### ")
    print(f"####### Path {path}")
    with open(path, 'r') as fin:
        print(fin.read(), end="")
    print("##################### END OF FILE OUTPUT ##################### ")
