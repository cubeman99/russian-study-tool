
def hexify(byte_string: bytes):
    return " ".join("{:02X}".format(x) for x in byte_string)

