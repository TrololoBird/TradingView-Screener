from __future__ import annotations

from metainfo_loader import download_all
from openapi_generator import generate_from_metainfo


def main() -> None:
    markets = download_all()
    for market in markets:
        path = generate_from_metainfo(market)
        print(f'Generated {path}')


if __name__ == '__main__':
    main()
