#!/usr/bin/env python
"""Update the x-indicators section in the sample YAML."""
from pathlib import Path
import yaml
from collect_indicators import collect_indicators

YAML_PATH = Path('samples/numeric_indicator_api_sample.yaml')


def main() -> None:
    names = collect_indicators(Path('data/metainfo'))
    data = yaml.safe_load(YAML_PATH.read_text())
    data['components']['x-indicators'] = names
    YAML_PATH.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    )


if __name__ == '__main__':
    main()
