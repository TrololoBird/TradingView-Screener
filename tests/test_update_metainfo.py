import json
import importlib.util
from pathlib import Path

# Load the update_metainfo script as a module
SCRIPT_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'update_metainfo.py'
spec = importlib.util.spec_from_file_location('update_metainfo', SCRIPT_PATH)
update_metainfo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update_metainfo)


def test_update_metainfo(monkeypatch, tmp_path):
    markets_path = Path(__file__).resolve().parents[1] / 'data' / 'markets.json'
    markets_data = json.loads(markets_path.read_text())
    markets = markets_data.get('countries', []) + markets_data.get('other', [])

    meta_dir = tmp_path / 'metainfo'
    monkeypatch.setattr(update_metainfo, 'METAINFO_DIR', meta_dir)
    monkeypatch.setattr(update_metainfo, 'MARKETS_PATH', markets_path)

    call_order = []

    def fake_post(url, json=None, headers=None):
        call_order.append(('post', url))

        class Resp:
            def __init__(self, text):
                self.text = text

            def raise_for_status(self):
                pass

        return Resp(f'data for {url}')

    monkeypatch.setattr(update_metainfo.requests, 'post', fake_post)

    def fake_run(args, check=False):
        call_order.append(('run', args))

    monkeypatch.setattr(update_metainfo.subprocess, 'run', fake_run)

    update_metainfo.main()

    get_calls = [c for c in call_order if c[0] == 'post']
    run_calls = [c[1] for c in call_order if c[0] == 'run']

    assert len(get_calls) == len(markets)
    assert run_calls == [
        [
            'python',
            'scripts/gpt_openapi_generator.py',
        ]
    ]
    assert call_order[-1][0] == 'run'

    for market in markets:
        path = meta_dir / f'{market}.json'
        assert path.exists()
        assert path.read_text() == f'data for https://scanner.tradingview.com/{market}/metainfo'
