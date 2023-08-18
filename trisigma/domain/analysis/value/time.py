from trisigma import dtype
from trisigma import lib
from typing import Union, List, Optional
from trisigma import const

import pandas as pd
from datetime import datetime, timedelta, date
import math

TIMEUNITS = {
    const.SECOND: 's',
    const.MINUTE: 'm',
    const.HOUR: 'h',
    const.DAY: 'd',
    const.WEEK: 'w',
    const.YEAR: 'y'
}

class Interval:

    seconds: int
    coef: int
    unit: int

    def __init__(
        self,
        interval: dtype.Duration
    ):
        self.seconds = convert_duration(interval)
        self.unit = lib.duration.find_best_timeunit(self.seconds)
        self.coef = int(self.seconds / self.unit)

    def __str__(self):
        return self.strf("{coef}{unit}")

    def __repr__(self):
        return f"Interval({self.__str__()})"

    def __int__(self):
        return self.seconds

    def __float__(self, other):
        return float(self.seconds)

    def floor(self, epoch: int):
        floored = epoch - (epoch % self.seconds)
        return floored

    @staticmethod
    def parse(duration: str):
        return Interval(duration)

    def strf(self, fmt, units={}):
        unit = units.get(self.unit, TIMEUNITS[self.unit])
        coef = self.coef
        return fmt.format(coef=coef, unit=unit)

    def to_pandas_str(self):
        units = {
            const.MINUTE: "T",
            const.HOUR: "H",
            const.DAY: "D",
            const.WEEK: "W",
            const.YEAR: "Y"
        }
        intv = self.strf("{coef}{unit}", units)
        return intv

    def copy():
        return Interval(self.seconds)

def convert_duration(duration: dtype.Duration) -> int:
    if isinstance(duration, timedelta):
        return int(duration.total_seconds())
    elif isinstance(duration, int) or isinstance(duration, float):
        return int(duration)
    elif isinstance(duration, str):
        return lib.duration.parse_duration(duration)

class TimeSpan:

    start: datetime
    end: datetime
    duration: float

    def __init__(self, start: dtype.Datetype, end: Optional[dtype.Datetype] = None):
        self.start = convert_datetype(start)
        self.end = convert_datetype(end)
        self.duration = (self.end - self.start).total_seconds()

    def to_epoch(self):
        return int(self.start.timestamp()), int(self.end.timestamp())

    def to_dates(self):
        start = self.start.date()
        end = self.end.date()
        return start, end

    def to_datetime(self):
        return self.start, self.end

    def copy(self):
        return TimeSpan(self.start, self.end)

    def __contains__(self, other):
        dt = convert_datetype(other)
        return self.start <= dt <= self.end

    def __int__(self):
        return int(self.duration)

    def __float__(self):
        return float(self.duration)


def convert_datetype(dt: dtype.Datetype | None) -> datetime:
    if dt is None:
        return datetime.now()
    elif isinstance(dt, datetime):
        return dt
    elif isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time())
    elif isinstance(dt, int) or isinstance(dt, float):
        if int(math.log10(dt)) == 9:
            return datetime.fromtimestamp(dt)
        elif int(math.log10(dt)) == 12:
            return datetime.fromtimestamp(dt / 1000)
        else:
            raise Exception("Invalid timestamp")
    elif isinstance(dt, str):
        return datetime.fromisoformat(dt)
    else:
        raise Exception("Invalid Datetype")


from datetime import datetime

class BadIntervalError (Exception):
   pass

def floor(date, interval, delta=None) -> datetime:
    """Makes a floor rounding to the given date.
        eg. date = <2022-10-28:23-53-13>, interval = "15m" --> <2022-10-28:23-45-00>
            date = <2022-10-28:23-53-13>, interval = "1d" --> <2022-10-28:00-00-00>

    :param date: the date that will be rounded.
    :type date: <datetime.datetime> or <int> (as a timestamp)
    :param interval: the interval that will be used to round the date.
    :type interval: <str>
    :param delta: (Optional) adds offset to the rounding. eg: interval="1w", delta=timedelta(days=2) will round to the last Wednesday, instead of Monday.
    :type delta: <datetime.timedelta>
    """
    if delta != None:
        delta = delta.total_seconds()
    else:
        delta = 0
    if not isinstance(date, (int, float)):
        date = date.timestamp()
    units = {'w': (604800, 345600), 'd': (86400, 0),
                'h': (3600, 0), 'm': (60, 0), 's': (1, 0)}
    freq = int(''.join([i for i in interval if i.isdigit()]))
    unit = ''.join([i for i in interval if i.isalpha()])
    coef = units[unit][0] * freq
    delt = units[unit][1] + delta

    result = (date - delt) - ((date - delt) % coef) + delt
    return datetime.fromtimestamp(int(result))


def ceil(date, interval, delta=None) -> datetime:
    """Makes a ceil rounding to the given date.
        eg. date = <2022-10-28:23-53-13>, interval = "15m" --> <2022-10-29:00-00-00>
            date = <2022-10-28:23-53-13>, interval = "2d" --> <2022-10-30:00-00-00>

    :param date: the date that will be rounded.
    :type date: <datetime.datetime> or <int> (as a timestamp)
    :param interval: the interval that will be used to round the date.
    :type interval: <str>
    :param delta: (Optional) adds offset to the rounding. eg: interval="1w", delta=timedelta(days=2) will round to the next Wednesday, instead of Monday.
    :type delta: <datetime.timedelta>
    """

    if delta != None:
        delta = delta.total_seconds()
    else:
        delta = 0
    if not isinstance(date, (int, float)):
        date = date.timestamp()
    units = {'w': (604800, 345600), 'd': (86400, 0),
             'h': (3600, 0), 'm': (60, 0), 's': (1, 0)}
    freq = int(''.join([i for i in interval if i.isdigit()]))
    unit = ''.join([i for i in interval if i.isalpha()])
    coef = units[unit][0] * freq
    delt = units[unit][1] + delta

    result = (date - delt) - ((date - delt) % coef) + delt + coef
    return datetime.fromtimestamp(int(result))

