from __future__ import annotations

import re
import textwrap
import tradingview_screener
from pathlib import Path

import pandas as pd


def test_readme_examples():
    # resolve README path relative to the repository root
    readme = Path(__file__).resolve().parents[1] / 'README.md'
    source = readme.read_text(encoding='utf-8')

    matches = re.findall(r'(?<=```python)(.*?)(?=```)', source, re.DOTALL)

    snippets = []
    for match in matches:
        snippet_lines = []
        for line in match.splitlines():
            line = line.rstrip()
            if line.startswith('>>> '):
                line = line[4:]
            snippet_lines.append(line)
        snippets.append(textwrap.dedent('\n'.join(snippet_lines)))

    pd.options.display.max_rows = 10  # hard limit, even on small DFs

    for snippet in snippets:
        print(snippet)
        assert '>>>' not in snippet, 'cleaning failed'
        compile(snippet, '<readme>', 'exec')


if __name__ == '__main__':
    test_readme_examples()
