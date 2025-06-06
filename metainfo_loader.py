import json
import logging
from pathlib import Path
from typing import List, Optional

import requests

from tradingview_screener.query import HEADERS

MARKETS_PATH = Path('data/markets.json')
METAINFO_DIR = Path('data/metainfo')
META_URL = 'https://scanner.tradingview.com/{market}/metainfo'


def _read_markets(markets_path: Path) -> List[str]:
    data = json.loads(markets_path.read_text())
    return data.get('countries', []) + data.get('other', [])


def download_all(
    markets_path: Path | None = None,
    output_dir: Path | None = None,
    *,
    session: Optional[requests.sessions.Session] = None,
) -> List[str]:
    """Download metainfo for all markets and return the market list."""
    path = markets_path or MARKETS_PATH
    out = output_dir or METAINFO_DIR
    session = session or requests

    markets = _read_markets(path)
    out.mkdir(parents=True, exist_ok=True)
    successful: List[str] = []

    for market in markets:
        url = META_URL.format(market=market)
        try:
            resp = session.get(url, headers=HEADERS)
            resp.raise_for_status()
        except Exception as exc:
            logging.error('Failed to download %s: %s', url, exc)
            continue

        (out / f'{market}.json').write_text(resp.text, encoding='utf-8')
        successful.append(market)

    return successful


def download_metainfo(
    markets_path: Path | None = None,
    output_dir: Path | None = None,
    *,
    session: Optional[requests.sessions.Session] = None,
) -> List[str]:
    """Alias for backward compatibility."""
    return download_all(markets_path, output_dir, session=session)
