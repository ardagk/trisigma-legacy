import hashlib
import json

def dict_hash(d):
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode('utf-8')).hexdigest()

def dict_eq(d1, d2):
    return dict_hash(d1) == dict_hash(d2)


