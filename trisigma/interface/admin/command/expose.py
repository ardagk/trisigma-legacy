import inspect
from . import command_handler

def expose(name: str | None = None, prefix: str | None = None, namespace: str | None = None):
    """Decorator to register a function to be called when a that functions name is received. Any
    additional args are and kwargs (format: "kwarg=1") passed to the function. For instance methods
    use "Router.add" instead.

    :param pattern: The pattern to match against. If None, the function name is used.
    :type name: str
    :param regex: Whether or not to use regex matching
    :type regex: bool
    """

    def inner(func):
        nonlocal name
        name = name or func.__name__
        if prefix:
            name = prefix + '-' + name
        if namespace:
            name = "{namespace}/{name}".format(namespace=namespace, name=name)
            name = name.replace("//", "/")
        args = []
        kwargs = {}
        for param in inspect.signature(func).parameters.values():
            if param.default is param.empty:
                args.append(param.name)
            else:
                kwargs[param.name] = param.default
        command_handler.add(name, func, args, kwargs)
        return func
    return inner
