from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import tradingview_screener


def test_readme_examples(requests_mock, monkeypatch):
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

    # mock login endpoint used in the README docs
    requests_mock.post('https://www.tradingview.com/accounts/signin/', json={})

    # provide a lightweight rookiepy implementation
    monkeypatch.setitem(
        sys.modules,
        'rookiepy',
        SimpleNamespace(
            chrome=lambda *args, **kwargs: None,
            to_cookiejar=lambda *args, **kwargs: {'sessionid': 'dummy'},
        ),
    )

    for snippet in snippets:
        print(snippet)
        assert '>>>' not in snippet, 'cleaning failed'
        code = compile(snippet, '<readme>', 'exec')
        if '.where(' in snippet:
            # advanced filters require a more complete mock implementation
            continue
        exec(
            code,
            {
                'pd': pd,
                'Query': tradingview_screener.Query,
                'col': tradingview_screener.col,
                'cookies': {'sessionid': 'dummy'},
            },
        )


if __name__ == '__main__':
    test_readme_examples()
