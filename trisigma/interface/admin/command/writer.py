
import asyncio
import contextlib
import sys
import threading

default_writer = sys.stdout
tmp_writers = {}
refs = {}

def get_id():
    """ Returns an id unique to the asycio_task or thread"""
    try:
        return id(asyncio.get_event_loop())
    except RuntimeError:
        return id(threading.current_thread())

def get_writer():
    return tmp_writers.get(get_id(), default_writer)

def set_default_out(out):
    global default_writer
    default_writer = out

@contextlib.contextmanager
def pipeout(writer):
    """A thread-safe context manager directing 'commands.out' to a specific file-like object"""
    if get_id() in tmp_writers.keys():
        refs[get_id()] += 1
    else:
        refs[get_id()] = 1
        tmp_writers[get_id()] = writer
    yield
    tmp_writers[get_id()].flush()
    refs[get_id()] -= 1
    if refs[get_id()] == 0:
        del tmp_writers[get_id()]
        del refs[get_id()]

def out(msg='', end="\n", flush=True):
    """A thread-safe print function that prints to the current output"""
    get_writer().write(msg + end)
    if flush:
        get_writer().flush()

