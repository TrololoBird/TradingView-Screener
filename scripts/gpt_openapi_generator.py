import json
from pathlib import Path

from market_loader import get_markets
from openapi_generator import generate_spec
from tv_api_parser import fetch_metainfo, group_fields, sample_symbols

OUTPUT_DIR = Path("openapi_generated")
STATS_PATH = OUTPUT_DIR / "stats.json"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    markets = get_markets()
    stats = []
    for market in markets:
        try:
            meta = fetch_metainfo(market)
        except Exception as exc:
            stats.append({"market": market, "error": str(exc)})
            print(f"Failed to download metainfo for {market}: {exc}")
            continue

        fields = meta.get("fields", meta)
        visible = [f for f in fields if not f.get("hh") and not f.get("is_hidden")]
        no_tf, with_tf, tfs = group_fields(visible)
        all_fields = [f.get("n") for f in visible if f.get("n")]
        try:
            path = generate_spec(market, no_tf, with_tf, tfs, all_fields)
            print(f"Generated {path}")
        except Exception as exc:  # validation or YAML errors
            stats.append({"market": market, "error": str(exc)})
            print(f"Failed to build spec for {market}: {exc}")
            continue

        try:
            symbols = sample_symbols(market)
        except Exception:
            symbols = []
        stats.append({
            "market": market,
            "fields": len(all_fields),
            "symbols": len(symbols),
            "timeframes": len(tfs),
        })

    STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Stats saved to {STATS_PATH}")


if __name__ == "__main__":
    main()
