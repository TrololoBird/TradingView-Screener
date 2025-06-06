import json
import subprocess
from pathlib import Path
import sys

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from metainfo_loader import download_all

MARKETS_PATH = Path('data/markets.json')
METAINFO_DIR = Path('data/metainfo')


def main() -> None:
    download_all(markets_path=MARKETS_PATH, output_dir=METAINFO_DIR, session=requests)
    subprocess.run(['python', 'scripts/gpt_openapi_generator.py'], check=True)


if __name__ == '__main__':
    main()
