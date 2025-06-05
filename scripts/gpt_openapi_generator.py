import copy
import json
from pathlib import Path
from typing import List, Tuple

import requests
import yaml

from tradingview_screener.query import HEADERS

MARKETS_URL = "https://scanner.tradingview.com/markets"
METAINFO_URL = "https://scanner.tradingview.com/{market}/metainfo"
SCAN_URL = "https://scanner.tradingview.com/{market}/scan"

BASE_SPEC_PATH = Path("openapi.yaml")
MARKETS_PATH = Path("data/markets.json")
OUTPUT_DIR = Path("openapi_generated")


def get_markets() -> List[str]:
    """Return the list of available markets."""
    try:
        resp = requests.get(MARKETS_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("countries", []) + data.get("other", [])
    except Exception:
        data = json.loads(MARKETS_PATH.read_text())
        return data.get("countries", []) + data.get("other", [])


def fetch_metainfo(market: str) -> dict:
    resp = requests.post(METAINFO_URL.format(market=market), json={}, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def sample_symbol(market: str) -> List[str]:
    payload = {"symbols": {"query": {"types": []}}, "columns": ["s"], "range": [0, 1]}
    resp = requests.post(SCAN_URL.format(market=market), json=payload, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [row.get("s") for row in data.get("data", [])]


def group_fields(meta: dict) -> Tuple[List[str], List[str], List[str]]:
    columns = meta.get("columns", [])
    no_tf = sorted({c for c in columns if "|" not in c})
    tf_cols = [c for c in columns if "|" in c]
    bases = sorted({c.split("|")[0] for c in tf_cols})
    tfs = sorted({c.split("|")[1] for c in tf_cols})
    return no_tf, bases, tfs


def build_spec(market: str, base: dict, no_tf: List[str], with_tf: List[str], tfs: List[str]) -> dict:
    spec = copy.deepcopy(base)
    spec.setdefault("info", {})
    spec["info"]["title"] = f"TradingView Screener API — {market}"
    description = spec["info"].get("description", "")
    spec["info"]["description"] = description + "\nCompatible with GPT Custom Actions."

    op = {}
    if "paths" in spec:
        template = "/{market}/scan"
        if template in spec["paths"]:
            op = spec["paths"].pop(template)["post"]
        spec.pop("paths", None)

    parameters = (
        op.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {"$ref": "#/components/schemas/QueryDict"})
    )
    responses = op.get(
        "responses",
        {
            "200": {
                "description": "Screener results",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ScreenerDict"}}},
            }
        },
    )
    spec["functions"] = {
        f"scan_{market}": {
            "operationId": f"scan_{market}",
            "summary": op.get("summary", "Scan TradingView market"),
            "description": op.get("description", ""),
            "parameters": parameters,
            "responses": responses,
        }
    }

    comp = spec.setdefault("components", {}).setdefault("schemas", {})
    comp["NumericFieldNoTimeframe"] = {"type": "string", "enum": no_tf}
    pattern = f"^({'|'.join(with_tf)})\\|({'|'.join(tfs)})$" if with_tf and tfs else "^[A-Za-z0-9_.\\[\\]-]+\\|.*$"
    comp["NumericFieldWithTimeframe"] = {"type": "string", "pattern": pattern}

    spec["x-timeframes"] = tfs
    spec["x-fields"] = no_tf + [f"{b}|{tf}" for b in with_tf for tf in tfs]
    return spec


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    base = yaml.safe_load(BASE_SPEC_PATH.read_text())
    markets = get_markets()
    stats = []
    for market in markets:
        try:
            meta = fetch_metainfo(market)
        except Exception as exc:
            print(f"Failed to download metainfo for {market}: {exc}")
            continue
        no_tf, with_tf, tfs = group_fields(meta)
        spec = build_spec(market, base, no_tf, with_tf, tfs)
        out_path = OUTPUT_DIR / f"{market}.yaml"
        out_path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        print(f"Generated {out_path}")
        try:
            symbols = sample_symbol(market)
        except Exception:
            symbols = []
        stats.append({"market": market, "fields": len(no_tf) + len(with_tf), "symbols": len(symbols)})

    stats_path = OUTPUT_DIR / "stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Stats saved to {stats_path}")


if __name__ == "__main__":
    main()
