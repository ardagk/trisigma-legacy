from trisigma import dtype
from typing import Union, List, Optional
import pandas as pd
from .time import Interval
from datetime import datetime, timedelta

Rowtype = Union[dict, List[dict], pd.Series, pd.DataFrame]

def convert_rowtype(rows: Rowtype) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        return rows
    elif isinstance(rows, pd.Series):
        return rows.to_frame()
    elif isinstance(rows, dict):
        return pd.DataFrame([rows])
    elif isinstance(rows, list):
        return pd.DataFrame(rows)

class TimeWindow:

    size: int
    interval: Interval
    agg: dtype.Agg
    df: pd.DataFrame
    _df: pd.DataFrame
    current: pd.Series
    head_timestamp: int

    def __init__(self, interval, size, agg):
        self.interval = interval
        self.size = size
        self.agg = agg
        self.head_timestamp = 0
        self._df = pd.DataFrame()

    def __repr__(self):
        return repr(self._df)

    def __str__(self):
        return str(self._df)


    def _sanitize_incoming(self, rows: Rowtype):
        rows = convert_rowtype(rows).to_dict(orient='records')
        rows.sort(key=lambda x: x['time'], reverse=True)
        rows = list(
            filter(
                lambda x: x['time'] > self.head_timestamp,
                rows
            ))

        if len(rows) == 0:
            return
        df = convert_rowtype(rows)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df = df.set_index('time')
        df = df.drop_duplicates()
        df = df.resample(self.interval.to_pandas_str(), label='right').agg(self.agg)
        return df, rows[0]['time']

    def update(self, rows: Rowtype):
        df, new_head = self._sanitize_incoming(rows)
        self.head_timestamp = new_head
        if len(df) == 0: return
        self._df = pd.concat([df, self._df])
        self._df = self._df[::-1].resample(self.interval.to_pandas_str()).agg(self.agg).iloc[::-1]
        self._df = self._df.head(self.size)
        self.df = self._df.copy()
        assert self.df.index.is_monotonic_decreasing

    def fill(self, rows: List[dict] or pd.DataFrame):
        assert len(self._df) == 0
        df = dtindex(rows)
        df = resample(df, self.agg, self.interval)
        df = df.head(self.size)
        self._df = df
        self.df = self._df.copy()

def dtindex(rows: Rowtype) -> pd.DataFrame:
    """A df with pd.Timestamp as index in descending order"""
    df = convert_rowtype(rows)
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df = df.set_index('time')
    df = df.sort_index(ascending=False)
    df = df.drop_duplicates()
    return df

def resample(
        df: pd.DataFrame,
        agg: dict,
        interval: Interval,
        label='right',
        closed='right'
    ):
    assert df.index.is_monotonic_decreasing
    intv = interval.to_pandas_str()
    df = df[::-1].resample(intv, label=label, closed='right').agg(agg)[::-1]
    df = df.dropna()
    return df

class CandleWindow (TimeWindow):

    AGG = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }

    def __init__(self, interval: Interval, size: int):
        super().__init__(interval, size, CandleWindow.AGG)
