from datetime import datetime, timedelta, date
from typing import Union, TypedDict, Dict, Callable, Any

Datetype = Union[
    datetime,
    int,
    float,
    date
]
Duration = Union[timedelta, int, float, str]
Agg = Dict[str, Union[str, Callable[..., Any]]]


class OHLC (TypedDict):
    time: int
    open: str
    high: str
    low: str
    close: str

class OHLCV (TypedDict):
    time: int
    open: str
    high: str
    low: str
    close: str
    volume: str

__all__ = [
    'Datetype',
    'Duration',
    'Agg',
    'OHLC',
    'OHLCV'
]
