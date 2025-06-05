import json
import subprocess
from pathlib import Path

import requests

from tradingview_screener.query import HEADERS

MARKETS_PATH = Path('data/markets.json')
METAINFO_DIR = Path('data/metainfo')


def load_markets() -> list[str]:
    markets: list[str] = []
    if MARKETS_PATH.exists():
        data = json.loads(MARKETS_PATH.read_text())
        markets.extend(data.get('countries', []))
        markets.extend(data.get('other', []))
    if not markets:
        markets = [p.stem for p in METAINFO_DIR.glob('*.json')]
    return markets


def main() -> None:
    METAINFO_DIR.mkdir(parents=True, exist_ok=True)
    markets = load_markets()
    for market in markets:
        url = f'https://scanner.tradingview.com/{market}/meta'
        print(f'Downloading {url}')
        try:
            resp = requests.get(url, headers=HEADERS)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f'Failed to download {market}: {exc}')
            continue
        (METAINFO_DIR / f'{market}.json').write_text(resp.text, encoding='utf-8')

    subprocess.run(['python', 'scripts/generate_openapi.py'], check=True)


if __name__ == '__main__':
    main()
