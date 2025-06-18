from __future__ import annotations
import sys
import yaml
from fastapi.openapi.utils import get_openapi
from tradingview_screener.openapi import create_app, ScanRequest


def generate_for_market(market: str) -> None:
    # patch default markets for the ScanRequest
    ScanRequest.model_fields['markets'].default = [market]
    app = create_app()
    spec = get_openapi(title=f"TradingView Screener API - {market}", version="1.0.0", routes=app.routes)
    with open(f"specs/openapi_{market}.yaml", "w") as f:
        yaml.dump(spec, f, sort_keys=False)


def main() -> None:
    markets = sys.argv[1:] if len(sys.argv) > 1 else ["america", "crypto", "forex"]
    for market in markets:
        generate_for_market(market)


if __name__ == "__main__":
    main()
