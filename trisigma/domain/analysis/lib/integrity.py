import hashlib
import json

def hashkey(row):
    return hashlib.sha1(json.dumps(row, sort_keys=True).encode('utf-8')).hexdigest()
