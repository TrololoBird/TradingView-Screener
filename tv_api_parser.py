import json
from pathlib import Path
from typing import List, Tuple

import requests

from tradingview_screener.query import HEADERS

META_URL = 'https://scanner.tradingview.com/{market}/metainfo'
SCAN_URL = 'https://scanner.tradingview.com/{market}/scan'
METAINFO_DIR = Path('data/metainfo')


def fetch_metainfo(market: str) -> List[dict]:
    """Return metainfo JSON for a market."""
    try:
        resp = requests.post(META_URL.format(market=market), json={}, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        path = METAINFO_DIR / f'{market}.json'
        return json.loads(path.read_text())


def sample_symbols(market: str) -> List[str]:
    """Return a list of sample ticker symbols for a market."""
    payload = {'symbols': {'query': {'types': []}}, 'columns': ['s'], 'range': [0, 1]}
    try:
        resp = requests.post(
            SCAN_URL.format(market=market), json=payload, headers=HEADERS, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        return [row.get('s') for row in data.get('data', [])]
    except Exception:
        return []


def group_fields(meta: List[dict]) -> Tuple[List[str], List[str], List[str]]:
    """Return columns without timeframe, bases with timeframe and timeframes."""
    columns = [item.get('n') for item in meta if item.get('n')]
    no_tf = sorted({c for c in columns if '|' not in c})
    tf_cols = [c for c in columns if '|' in c]
    bases = sorted({c.split('|')[0] for c in tf_cols})
    tfs = sorted({c.split('|')[1] for c in tf_cols})
    return no_tf, bases, tfs
