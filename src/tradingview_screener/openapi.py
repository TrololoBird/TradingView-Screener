from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from tradingview_screener.query import Query as TVQuery

app = FastAPI(
    title="TradingView Screener API",
    version="1.0.0",
    description="FastAPI server exposing TradingView screener queries",
)

class ScanRequest(BaseModel):
    """Request body for the ``/scan`` endpoint."""

    markets: list[str] = Field(
        default=["america"],
        description="Markets to scan, e.g. ``['america']`` or ``['crypto']``.",
        json_schema_extra={"examples": [["america"], ["crypto"]]},
    )
    columns: list[str] = Field(
        default=["name", "close"],
        description="Columns to include in the response.",
        json_schema_extra={"examples": [["name", "close", "volume"]]},
    )
    limit: int = Field(
        default=50,
        description="Maximum number of rows to return.",
        json_schema_extra={"examples": [10]},
    )

class ScanResponse(BaseModel):
    """Response returned by the ``/scan`` endpoint."""

    count: int = Field(
        description="Total number of records matching the query.",
        json_schema_extra={"example": 17580},
    )
    data: list[dict] = Field(
        description="List of result rows.",
        json_schema_extra={
            "examples": [
                [
                    {"ticker": "NASDAQ:NVDA", "name": "NVDA", "close": 127.25},
                    {"ticker": "AMEX:SPY", "name": "SPY", "close": 558.7},
                ]
            ]
        },
    )

@app.post(
    "/scan",
    summary="Run a screener scan",
    response_model=ScanResponse,
    tags=["Scanner"],
)
def scan(req: ScanRequest) -> ScanResponse:
    """Query TradingView screener and return matching rows."""
    q = TVQuery().set_markets(*req.markets).select(*req.columns).limit(req.limit)
    count, df = q.get_scanner_data()
    return ScanResponse(count=count, data=df.to_dict(orient="records"))


def create_app() -> FastAPI:
    return app
