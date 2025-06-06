from __future__ import annotations

from market_loader import get_markets
from tv_api_parser import fetch_metainfo, group_fields
from openapi_generator import generate_spec


def main() -> None:
    markets = get_markets()
    for market in markets:
        try:
            meta = fetch_metainfo(market)
        except Exception as exc:
            print(f'Failed to get metainfo for {market}: {exc}')
            continue
        no_tf, with_tf, tfs = group_fields(meta)
        path = generate_spec(market, no_tf, with_tf, tfs)
        print(f'Generated {path}')


if __name__ == '__main__':
    main()
