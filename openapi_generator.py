from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import List

import yaml
from openapi_spec_validator.shortcuts import validate_spec

from tv_api_parser import group_fields


def _load_fields(meta: dict | list) -> list[dict]:
    """Return list of field dictionaries from metainfo JSON."""
    if isinstance(meta, dict):
        fields = meta.get('fields', [])
    else:
        fields = meta
    if not isinstance(fields, list):
        return []
    return fields

BASE_SPEC_PATH = Path('openapi.yaml')
OUTPUT_DIR = Path('openapi_generated')
METAINFO_DIR = Path('data/metainfo')


def build_spec(
    market: str,
    base: dict,
    no_tf: List[str],
    with_tf: List[str],
    tfs: List[str],
    all_fields: List[str],
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

    qdict_schema = (
        op.get('requestBody', {})
        .get('content', {})
        .get('application/json', {})
        .get('schema', {'$ref': '#/components/schemas/QueryDict'})
    )

    func_params = {'type': 'object'}

    # extract subset for GPT functions
    props = {}
    if isinstance(qdict_schema, dict):
        qprops = qdict_schema.get('properties', {})
        props = {
            'symbols': qprops.get('symbols', {}),
            'columns': qprops.get('columns', {}),
            'filter': qprops.get('filter', {}),
            'sort': qprops.get('sort', {}),
            'range': qprops.get('range', {}),
        }
    if props:
        func_params['properties'] = props
        func_params['required'] = []
    else:
        func_params = qdict_schema
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
            'parameters': func_params,
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

    # add filter and sort enums
    filt = comp.get('FilterOperation')
    if filt:
        left = filt.get('properties', {}).get('left', {})
        left['enum'] = all_fields
        if all_fields:
            left.setdefault('examples', [all_fields[0]])

    sort_schema = comp.get('SortBy')
    if sort_schema:
        sort_by = sort_schema.get('properties', {}).get('sortBy', {})
        sort_by['enum'] = all_fields
        if all_fields:
            sort_by.setdefault('examples', [all_fields[0]])

    spec['x-timeframes'] = tfs
    spec['x-fields'] = no_tf + combos
    spec['x-all-fields'] = all_fields
    return spec


def generate_spec(
    market: str,
    no_tf: List[str],
    with_tf: List[str],
    tfs: List[str],
    all_fields: List[str],
) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    base = yaml.safe_load(BASE_SPEC_PATH.read_text())
    spec = build_spec(market, base, no_tf, with_tf, tfs, all_fields)
    out_path = OUTPUT_DIR / f'{market}.yaml'
    out_path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
    # validate without the non standard `functions` field
    to_validate = copy.deepcopy(spec)
    to_validate.pop('functions', None)
    validate_spec(to_validate)
    return out_path


def generate_from_metainfo(market: str) -> Path:
    """Generate OpenAPI spec for a market using stored metainfo."""
    path = METAINFO_DIR / f"{market}.json"
    meta = json.loads(path.read_text())
    fields = _load_fields(meta)
    visible = [f for f in fields if not f.get('hh') and not f.get('is_hidden')]
    all_fields = [item.get('n') for item in visible if item.get('n')]
    no_tf, with_tf, tfs = group_fields(visible)
    return generate_spec(market, no_tf, with_tf, tfs, all_fields)
