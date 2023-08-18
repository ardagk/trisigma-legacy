from typing import Callable

callbacks = {
    "on_add": [],
    "on_unknown_cmd": [lambda e: "Command not found: " + str(e)],
    "on_cmd_err": [lambda e: "Error: " + str(e)],
    "on_parse_err": [lambda e: "Invalid arguments: " + str(e)],
    "on_cmd_success": [lambda o: o],
    "pre_parse": [lambda line: line]
}
def set_callback(event_name: str, callback: Callable):
    if event_name not in callbacks:
        raise ValueError(f"Event '{event_name}' not found")
    callbacks[event_name].insert(0, callback)

def call(event_name: str, *args, **kwargs):
    callback = callbacks[event_name]
    if callback:
        for cb in callback:
            cb(*args, **kwargs)

def callfirst(event_name: str, *args, **kwargs):
    callback = callbacks[event_name]
    if callback:
        return callback[0](*args, **kwargs)

