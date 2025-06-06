from __future__ import annotations

import copy
from pathlib import Path
from typing import List

import yaml
from openapi_spec_validator.shortcuts import validate_spec

BASE_SPEC_PATH = Path('openapi.yaml')
OUTPUT_DIR = Path('openapi_generated')


def build_spec(
    market: str, base: dict, no_tf: List[str], with_tf: List[str], tfs: List[str]
) -> dict:
    spec = copy.deepcopy(base)
    info = spec.setdefault('info', {})
    info['title'] = f'TradingView Screener API — {market}'
    info['description'] = info.get('description', '') + '\nCompatible with GPT Custom Actions.'

    op = {}
    if 'paths' in spec:
        template = '/{market}/scan'
        if template in spec['paths']:
            op = spec['paths'].pop(template)['post']
        spec.pop('paths', None)

    parameters = (
        op.get('requestBody', {})
        .get('content', {})
        .get('application/json', {})
        .get('schema', {'$ref': '#/components/schemas/QueryDict'})
    )
    responses = op.get(
        'responses',
        {
            '200': {
                'description': 'Screener results',
                'content': {
                    'application/json': {'schema': {'$ref': '#/components/schemas/ScreenerDict'}}
                },
            }
        },
    )
    spec['functions'] = {
        f'scan_{market}': {
            'operationId': f'scan_{market}',
            'summary': op.get('summary', 'Scan TradingView market'),
            'description': op.get('description', ''),
            'parameters': parameters,
            'responses': responses,
        }
    }

    comp = spec.setdefault('components', {}).setdefault('schemas', {})
    comp['IndicatorWithoutTimeframe'] = {
        'type': 'string',
        'enum': no_tf,
        'examples': no_tf[:1],
    }
    combos = [f'{b}|{tf}' for b in with_tf for tf in tfs]
    comp['IndicatorWithTimeframe'] = {
        'type': 'string',
        'enum': combos,
        'examples': combos[:1],
    }

    qdict = comp.get('QueryDict')
    if qdict:
        cols = qdict.get('properties', {}).get('columns', {})
        cols['items'] = {
            'anyOf': [
                {'$ref': '#/components/schemas/IndicatorWithTimeframe'},
                {'$ref': '#/components/schemas/IndicatorWithoutTimeframe'},
            ]
        }
        if combos:
            cols['examples'] = [combos[0]]
        elif no_tf:
            cols['examples'] = [no_tf[0]]

    spec['x-timeframes'] = tfs
    spec['x-fields'] = no_tf + combos
    return spec


def generate_spec(market: str, no_tf: List[str], with_tf: List[str], tfs: List[str]) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    base = yaml.safe_load(BASE_SPEC_PATH.read_text())
    spec = build_spec(market, base, no_tf, with_tf, tfs)
    out_path = OUTPUT_DIR / f'{market}.yaml'
    out_path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
    # validate without the non standard `functions` field
    to_validate = copy.deepcopy(spec)
    to_validate.pop('functions', None)
    validate_spec(to_validate)
    return out_path
