class Sink:
    def __init__(self, out, enc):
        self.out = out
        self.enc = enc

    def write(self, x):
        self.out.write(x.encode(self.enc, "xmlcharrefreplace"))

    def close(self):
        pass


class SinkRaw:
    def __init__(self, out, enc):
        self.out = out
        self.enc = enc

    def write(self, x):
        self.out.write(x)

    def close(self):
        pass

    def __enter__(self):
        assert self.out
        return self.out

    def __exit__(self, *excinfo):
        self.close()


class HashSink:
    __slots__ = ("digest",)

    def __init__(self, h=None):
        if not h:
            from hashlib import md5

            h = md5()
        self.digest = h

    def write(self, x: bytes):
        self.digest.update(x)


class HashSinkText(HashSink):
    __slots__ = ("digest",)

    def write(self, x: str):
        self.digest.update(x.encode())
