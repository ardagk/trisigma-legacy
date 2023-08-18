import shlex
import logging
from typing import Callable
from .command import Command
from . import callbacks

logger = logging.getLogger("main")

__registry = { "hi": [Command(lambda: "hi", [], {})], }

def add(pattern: str, func, args, kwargs):
    #TODO: Option to register as regex.
    if not callable(func):
        raise TypeError("Function must be callable")
    if pattern not in __registry:
        __registry[pattern] = []

    command = Command(func, args, kwargs)
    __registry[pattern].append(command)
    callbacks.call("on_add", pattern, command)

class CommandNotFoundException(Exception):...

def exists(pattern):
    lexed = shlex.split(pattern)
    return lexed and search(lexed[0]) != []

def execute(
    args: list,
    #line: str,
    index: int=0,
    unknown_cmd_callback: Callable | None = None,
    parse_err_callback: Callable | None = None,
    cmd_err_callback: Callable | None = None,
    on_success_callback: Callable | None = None,
    raise_exceptions: bool = False,
):
    """
    processed = callbacks.callfirst("pre_parse", line)
    if processed: line = processed
    split = shlex.split(line)
    """
    split = args
    if not split: return
    pattern = split[0]
    argv = split[1:]
    commands = search(pattern)
    try:
        if commands == []:
            raise CommandNotFoundException(f"Command '{pattern}' not found")
        cmd = commands[index]
        args, kwargs = cmd.parse(argv)
        try:
            o = cmd(*args, **kwargs)
            if on_success_callback:
                o = on_success_callback(o)
            else:
                o = callbacks.callfirst("on_cmd_success", o)
            return o
        except Exception as e:
            if raise_exceptions: raise
            if cmd_err_callback is not None:
                return cmd_err_callback(e)
            else:
                return callbacks.callfirst("on_cmd_err", e)

    except CommandNotFoundException as e:
        if raise_exceptions: raise
        if unknown_cmd_callback is not None:
            return unknown_cmd_callback(e)
        else:
            return callbacks.callfirst("on_unknown_cmd", e)
    except Exception as e:
        if raise_exceptions: raise
        if parse_err_callback is not None:
            return parse_err_callback(e)
        else:
            return callbacks.callfirst("on_parse_err", e)

def search(pattern):
    """Makes a search for a pattern in the registry"""
    #TODO: Implement a regex search
    return __registry.get(pattern, [])

def get_commands():
    return list(__registry.keys())



