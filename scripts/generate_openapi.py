from __future__ import annotations

import os

import yaml
from fastapi.openapi.utils import get_openapi

from tradingview_screener.openapi import create_app


def main() -> None:
    app = create_app()
    spec = get_openapi(title=app.title, version="1.0.0", routes=app.routes)
    os.makedirs("specs", exist_ok=True)
    with open("specs/openapi.yaml", "w") as f:
        yaml.dump(spec, f, sort_keys=False)
    with open("specs/bundle.yaml", "w") as f:
        yaml.dump(spec, f, sort_keys=False)


if __name__ == "__main__":
    main()
