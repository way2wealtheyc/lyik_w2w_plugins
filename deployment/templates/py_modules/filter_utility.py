import base64
def to_base64(s):
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")