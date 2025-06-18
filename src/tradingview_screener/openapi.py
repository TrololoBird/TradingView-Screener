from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from tradingview_screener.query import Query as TVQuery

app = FastAPI(title="TradingView Screener API")

class ScanRequest(BaseModel):
    markets: list[str] = ["america"]
    columns: list[str] = ["name", "close"]
    limit: int = 50

@app.post("/scan")
def scan(req: ScanRequest):
    q = TVQuery().set_markets(*req.markets).select(*req.columns).limit(req.limit)
    count, df = q.get_scanner_data()
    return {"count": count, "data": df.to_dict(orient="records")}


def create_app() -> FastAPI:
    return app
