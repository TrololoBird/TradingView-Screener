import json
from pathlib import Path
import copy
import yaml

BASE_SPEC_PATH = Path('openapi.yaml')
METAINFO_DIR = Path('data/metainfo')


def load_fields(market: str) -> list[str]:
    data = json.loads((METAINFO_DIR / f'{market}.json').read_text())
    return [item['n'] for item in data if 'n' in item]


def generate_spec_for_market(market: str) -> None:
    base = yaml.safe_load(BASE_SPEC_PATH.read_text())
    spec = copy.deepcopy(base)
    # move path and remove MarketPath parameter
    path_template = '/{market}/scan'
    market_path = f'/{market}/scan'
    if path_template in spec['paths']:
        spec['paths'][market_path] = spec['paths'].pop(path_template)
    op = spec['paths'][market_path]['post']
    op['parameters'] = [
        p for p in op.get('parameters', []) if 'MarketPath' not in p.get('$ref', '')
    ]
    spec['info']['title'] = f'TradingView Screener API - {market}'
    spec['x-fields'] = load_fields(market)
    Path(f'openapi_{market}.yaml').write_text(
        yaml.safe_dump(spec, sort_keys=False, allow_unicode=True)
    )


def main() -> None:
    for file in METAINFO_DIR.glob('*.json'):
        generate_spec_for_market(file.stem)


if __name__ == '__main__':
    main()
