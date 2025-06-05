import pandas as pd
import pytest

from tradingview_screener.query import Query, DEFAULT_RANGE

@pytest.fixture(autouse=True)
def mock_get_scanner_data(monkeypatch):
    def fake_get_scanner_data(self, **kwargs):
        columns = list(self.query.get('columns', []))
        sort = self.query.get('sort')
        if sort:
            sort_col = sort['sortBy']
            if sort_col not in columns:
                columns.append(sort_col)
        start, end = self.query.get('range', DEFAULT_RANGE.copy())
        if end < start or start < 0:
            from requests import HTTPError
            raise HTTPError('invalid range')
        count_requested = end - start
        data_list = []
        for i in range(start, start + count_requested):
            low = 100 + i
            high = 200 + i
            close = low * 1.5
            vwap = low * 1.2
            div_yield = None if i % 2 == 0 else i * 0.1
            row_vals = []
            for col in columns:
                if col == 'close':
                    row_vals.append(close)
                elif col == 'price_52_week_low':
                    row_vals.append(low)
                elif col == 'price_52_week_high':
                    row_vals.append(high)
                elif col == 'VWAP':
                    row_vals.append(vwap)
                elif col == 'dividends_yield_current':
                    row_vals.append(div_yield)
                else:
                    row_vals.append(i)
            data_list.append({'s': f'T{i}', 'd': row_vals})
        df = pd.DataFrame(
            data=([row['s'], *row['d']] for row in data_list),
            columns=['ticker', *columns],
        )
        filter_list = self.query.get('filter')
        if filter_list:
            filt = filter_list[0]
            op = filt['operation']
            left = filt['left']
            right = filt['right']
            if op == 'above%':
                other_col, pct = right
                df = df[df[left] > df[other_col] * pct]
            elif op == 'below%':
                other_col, pct = right
                df = df[df[left] < df[other_col] * pct]
            elif op == 'in_range%':
                other_col, pct1, pct2 = right
                df = df[df[left].between(df[other_col] * pct1, df[other_col] * pct2)]
            elif op == 'not_in_range%':
                other_col, pct1, pct2 = right
                df = df[~df[left].between(df[other_col] * pct1, df[other_col] * pct2)]
        if sort:
            col_name = sort['sortBy']
            ascending = sort['sortOrder'] == 'asc'
            na_position = 'first' if sort.get('nullsFirst') else 'last'
            if col_name not in df.columns:
                df[col_name] = range(len(df))
            df = df.sort_values(col_name, ascending=ascending, na_position=na_position, ignore_index=True)
        count = len(df)
        return count, df
    monkeypatch.setattr(Query, 'get_scanner_data', fake_get_scanner_data)
    yield
