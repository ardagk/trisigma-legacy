from typing import Callable
import asyncio
import json
import functools
import hashlib
import logging
from trisigma import lib

class FlagException(Exception):
    pass

def _flag_actions(fn):

    #@functools.wraps(fn)
    async def wrapper(*args, raise_=False, **kwargs):
        name = fn.__name__
        logging.debug(f"Flag {name} created")
        res = await fn(*args, **kwargs)
        if raise_:
            logging.debug(f"Flag {name} raised")
            raise FlagException(res)
        else:
            logging.debug(f"Flag {name} triggered")
        return res
    return wrapper

def _gettable(value):
    if hasattr(value, 'get'):
        return value
    elif isinstance(value, Callable):
        valfunc = value
    else:
        valfunc = lambda: value
    class Gettable:
        def get(self):
            return valfunc()
    return Gettable()

@_flag_actions
async def crossover(a, b, **kwargs):
    a = _gettable(a)
    b = _gettable(b)
    while True:
        a_val = a.get()
        b_val = b.get()
        if a_val > b_val:
            await asyncio.sleep(0.1)
        else:
            return

@_flag_actions
async def trailing_stop(value, perc, **kwargs):
    value = _gettable(value)
    perc = _gettable(perc)
    perc_ = perc.get()
    trail = value.get() * perc_
    assert perc_ > 0 and perc_ < 2 and float(perc_) != 1.0
    while True:
        perc_ = perc.get()
        assert perc_ > 0 and perc_ < 2 and float(perc_) != 1.0
        value_ = value.get()
        d = -1 if perc_ > 1 else 1
        if value_ * perc_ * d > trail * d:
            trail = value_ * perc_
        if d * value_ <= d * trail:
            return
        else:
            await asyncio.sleep(0)

@_flag_actions
async def boolean(*fns, **kwargs):
    while True:
        if all(fn() is True for fn in fns):
            return
        await asyncio.sleep(0)

@_flag_actions
async def change(value, **kwargs):
    value = _gettable(value)
    last_val = value.get()
    while True:
        val = value.get()
        if not lib.dict_eq(val, last_val):
            return
        await asyncio.sleep(0)

@_flag_actions
async def chain(flags):
    for flag in flags:
        await flag
    return
