import json
import copy
from pathlib import Path
from typing import List, Tuple

import requests
import yaml

from tradingview_screener.query import HEADERS

MARKETS_URL = "https://scanner.tradingview.com/markets"
META_URL = "https://scanner.tradingview.com/{market}/meta"
OUTPUT_DIR = Path("openapi_generated")
BASE_SPEC_PATH = Path("openapi.yaml")
MARKETS_PATH = Path("data/markets.json")

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

def fetch_metainfo(market: str) -> List[dict]:
    resp = requests.get(META_URL.format(market=market), headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()

def group_fields(meta: List[dict]) -> Tuple[List[str], List[str], List[str]]:
    columns = [item.get("n") for item in meta if item.get("n")]
    no_tf = sorted({c for c in columns if "|" not in c})
    tf_columns = [c for c in columns if "|" in c]
    bases = sorted({c.split("|")[0] for c in tf_columns})
    tfs = sorted({c.split("|")[1] for c in tf_columns})
    return no_tf, bases, tfs

def build_spec(market: str, base: dict, no_tf: List[str], with_tf: List[str], tfs: List[str]) -> dict:
    spec = copy.deepcopy(base)
    spec["info"]["title"] = f"TradingView Screener API — {market}"
    spec.setdefault("info", {})
    description = spec["info"].get("description", "")
    spec["info"]["description"] = description + "\nCompatible with GPT Custom Actions."
    # convert paths -> functions
    if "paths" in spec:
        path = "/{market}/scan"
        if path in spec["paths"]:
            op = spec["paths"][path]["post"]
        else:
            op = {}
        spec.pop("paths")
    else:
        op = {}
    parameters = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {"$ref": "#/components/schemas/QueryDict"})
    responses = op.get("responses", {"200": {"description": "Screener results", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ScreenerDict"}}}}})
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
    comp["NumericFieldNoTimeframe"] = {
        "type": "string",
        "enum": no_tf,
    }
    if with_tf and tfs:
        pattern = f"^({'|'.join(with_tf)})\\|({'|'.join(tfs)})$"
    else:
        pattern = "^[A-Za-z0-9_.\\[\\]-]+\\|.*$"
    comp["NumericFieldWithTimeframe"] = {
        "type": "string",
        "pattern": pattern,
    }
    spec["x-timeframes"] = tfs
    return spec

def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    base = yaml.safe_load(BASE_SPEC_PATH.read_text())
    markets = get_markets()
    for market in markets:
        try:
            meta = fetch_metainfo(market)
        except Exception as e:
            print(f"Failed to download metainfo for {market}: {e}")
            continue
        no_tf, with_tf, tfs = group_fields(meta)
        spec = build_spec(market, base, no_tf, with_tf, tfs)
        out_path = OUTPUT_DIR / f"{market}.yaml"
        out_path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        print(f"Generated {out_path}")

if __name__ == "__main__":
    main()
