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
        resp = requests.get(META_URL.format(market=market), headers=HEADERS, timeout=10)
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
    """Return visible numeric columns and supported timeframes."""
    no_tf: set[str] = set()
    bases: set[str] = set()
    tfs: set[str] = set()

    for item in meta:
        name = item.get('n')
        if not name:
            continue
        if item.get('hh') or item.get('is_hidden'):
            continue
        typ = item.get('t')
        if typ not in {'number', 'price', 'percent', 'fundamental_price', 'bool'}:
            continue

        if '|' in name:
            base, tf = name.split('|', 1)
            if item.get('interval_dependent') is False:
                continue
            bases.add(base)
            tfs.add(tf)
        else:
            no_tf.add(name)

    return sorted(no_tf), sorted(bases), sorted(tfs)
