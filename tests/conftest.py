import json
import re
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def sample_response():
    path = Path(__file__).parent / "fixtures" / "sample_response.json"
    return json.loads(path.read_text())


@pytest.fixture(autouse=True)
def _mock_tv_api(requests_mock):
    def build_response(request, context):
        query = request.json()

        rng = query.get("range", [0, 50])
        if rng[1] < 0:
            context.status_code = 400
            context.reason = "Bad Request"
            return {"error": "invalid range"}

        columns = query.get(
            "columns",
            ["name", "close", "volume", "market_cap_basic"],
        )
        count = rng[1] - rng[0]

        def gen_value(col: str, i: int):
            if col == "name":
                return f"Name{i}"
            if col == "close":
                return 100 + i
            if col == "volume":
                return 1000 + i
            if col == "market_cap_basic":
                return float(i)
            if col == "dividends_yield_current":
                return None if i % 2 == 0 else i / 10
            if col == "price_52_week_low":
                return 80 + i
            if col == "price_52_week_high":
                return 200 + i
            if col == "VWAP":
                return 90 + i
            if col == "type":
                return ["stock", "stock", "dr", "fund", "structured"][i % 5]
            if col == "typespecs":
                return [["common"], ["preferred"], [], ["etf"], ["etn"]][i % 5]
            return i

        data = [
            {"s": f"SYM{i}", "d": [gen_value(c, i) for c in columns]}
            for i in range(count)
        ]

        for flt in query.get("filter", []):
            op = flt["operation"]
            left = flt["left"]
            right_col, pct = flt["right"][0], flt["right"][1]

            if op == "above%" and left == right_col and pct == 1:
                return {"totalCount": 0, "data": []}

            if left in columns and right_col in columns:
                li = columns.index(left)
                ri = columns.index(right_col)
                for row in data:
                    rv = row["d"][ri]
                    if op == "above%":
                        row["d"][li] = rv * pct + 1
                    elif op == "below%":
                        row["d"][li] = rv * pct - 1
                    elif op == "in_range%":
                        pct2 = flt["right"][2]
                        row["d"][li] = rv * (pct + pct2) / 2
                    elif op == "not_in_range%":
                        pct2 = flt["right"][2]
                        row["d"][li] = rv * (pct2 + 1)

        sort = query.get("sort")
        if sort and sort.get("sortBy") in columns:
            idx = columns.index(sort["sortBy"])
            nulls_first = sort.get("nullsFirst", False)

            def key(row):
                val = row["d"][idx]
                if val is None:
                    return (-1 if nulls_first else 1, 0)
                return (0, val)

            data.sort(key=key, reverse=sort.get("sortOrder") == "desc")

        context.status_code = 200
        return {"totalCount": 1000, "data": data}

    requests_mock.post(
        re.compile(r"https://scanner\.tradingview\.com/.*/scan"),
        json=build_response,
    )

