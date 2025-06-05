import json
import subprocess
from pathlib import Path

import requests

from tradingview_screener.query import HEADERS

MARKETS_PATH = Path('data/markets.json')
METAINFO_DIR = Path('data/metainfo')


def main() -> None:
    markets_data = json.loads(MARKETS_PATH.read_text())
    markets = markets_data.get('countries', []) + markets_data.get('other', [])
    METAINFO_DIR.mkdir(parents=True, exist_ok=True)
    for market in markets:
        url = f'https://scanner.tradingview.com/{market}/meta'
        print(f'Downloading {url}')
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        (METAINFO_DIR / f'{market}.json').write_text(resp.text)

    subprocess.run(['python', 'scripts/generate_openapi.py'], check=True)


if __name__ == '__main__':
    main()
