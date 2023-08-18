import hashlib

def get_unique_order_id(platform: str, order_id: int) -> int:
    s = "{platform}:{order_id}".format(
        platform=platform.upper(),
        order_id=order_id
    )
    hash = int(hashlib.sha1(s.encode()).hexdigest(), 16) % (10 ** 8)
    return hash
