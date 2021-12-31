import requests, json, os, tarfile
from tqdm import tqdm
from urllib.parse import urlparse
from pathlib import Path


def download(url, fname):
    print(f"Start download of {url}")
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


def extract(file, target):
    print(f"Start extractio of {file}")
    with tarfile.open(file) as f:
        f.extractall(target)


with open('toolchain-metadata.json') as f:
    data = json.load(f)
    urls = data['urls']
    base_path = Path(data['base-path'])
    base_path.mkdir(parents=True, exist_ok=True)
    for url in urls:
        a = urlparse(url)
        file_name = os.path.basename(a.path)
        target_path = str(base_path.joinpath(Path(file_name)).resolve())
        download(url, target_path)
        extract(target_path, base_path)
        os.remove(target_path)
