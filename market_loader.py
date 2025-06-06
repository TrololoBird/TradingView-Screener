import json
from pathlib import Path
from typing import List

import requests

from tradingview_screener.query import HEADERS

MARKETS_URL = 'https://scanner.tradingview.com/markets'
MARKETS_PATH = Path('data/markets.json')


def get_markets() -> List[str]:
    """Return available markets from TradingView or local cache."""
    try:
        resp = requests.get(MARKETS_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get('countries', []) + data.get('other', [])
    except Exception:
        data = json.loads(MARKETS_PATH.read_text())
        return data.get('countries', []) + data.get('other', [])
