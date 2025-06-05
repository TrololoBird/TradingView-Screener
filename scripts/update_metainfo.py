import subprocess
from pathlib import Path

import requests

from tradingview_screener.query import HEADERS

METAINFO_DIR = Path('data/metainfo')


def main() -> None:
    METAINFO_DIR.mkdir(parents=True, exist_ok=True)
    markets = [p.stem for p in METAINFO_DIR.glob('*.json')]
    for market in markets:
        url = f'https://scanner.tradingview.com/{market}/meta'
        print(f'Downloading {url}')
        try:
            resp = requests.get(url, headers=HEADERS)
            resp.raise_for_status()
        except requests.HTTPError as exc:
            print(f'Failed to download {market}: {exc}')
            continue
        (METAINFO_DIR / f'{market}.json').write_text(resp.text)

    subprocess.run(['python', 'scripts/generate_openapi.py'], check=True)


if __name__ == '__main__':
    main()
