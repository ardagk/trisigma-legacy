"""
library to parse hostname into proto, host, and port
"""

import urllib.parse


def parse_host(host: str, default_proto: str, default_port: int = None) -> (str, str, int):
    """
    parse hostname into proto, host, and port
    """
    proto = default_proto
    port = default_port
    if '://' in host:
        proto, host = host.split('://')
    if ':' in host:
        host, port = host.split(':')
    if port is not None:
        port = int(port)
    return proto, host, port


