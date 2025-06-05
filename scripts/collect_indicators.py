import json
from pathlib import Path


def collect_indicators(path: Path = Path('data/metainfo')) -> list[str]:
    names = set()
    for file in path.glob('*.json'):
        data = json.loads(file.read_text())
        for item in data:
            if 'n' in item and item['n']:
                names.add(item['n'])
    return sorted(names)


def main() -> None:
    for name in collect_indicators():
        print(name)


if __name__ == '__main__':
    main()
