import os
import struct
import sys

class BinaryReader():
    def __init__(self, fh):
        self.fh = fh

    def _debug(self, typ, data):
        if os.environ.get("DEBUG"):
            c_on = "\033[33m" if sys.stderr.isatty() else ""
            c_off = "\033[m" if sys.stderr.isatty() else ""
            print(c_on, "#", typ, repr(data), c_off, file=sys.stderr)
        return data

    def read(self, length):
        buf = self.fh.read(length)
        if len(buf) < length:
            if len(buf) == 0:
                raise EOFError("Hit EOF after 0/%d bytes" % length)
            else:
                raise IOError("Hit EOF after %d/%d bytes" % (len(buf), length))
        return self._debug("raw[%d]" % length, buf)

    def _read_fmt(self, length, fmt, typ):
        buf = self.fh.read(length)
        if len(buf) < length:
            if len(buf) == 0:
                raise EOFError("Hit EOF after 0/%d bytes" % length)
            else:
                raise IOError("Hit EOF after %d/%d bytes" % (len(buf), length))
        data, = struct.unpack(fmt, buf)
        return self._debug(typ, data)

    def read_u8(self):
        return self._read_fmt(1, "B", "byte")

    def read_u16_le(self):
        return self._read_fmt(2, "<H", "short")

    def read_u16_be(self):
        return self._read_fmt(2, ">H", "short")

    def read_u32_le(self):
        return self._read_fmt(4, "<L", "long")

    def read_u32_be(self):
        return self._read_fmt(4, ">L", "long")

    def read_u64_le(self):
        return self._read_fmt(8, "<Q", "quad")

    def read_u64_be(self):
        return self._read_fmt(8, ">Q", "quad")

class SshBinaryReader(BinaryReader):
    def read_bool(self):
        return self._read_fmt(1, "?", "bool")

    def read_uint32(self):
        return self.read_u32_be()

    def read_string(self):
        length = self.read_u32_be()
        return self.read(length)

    def read_array(self):
        string = self.read_string()
        return string.split(b",")

    def read_mpint(self):
        buf = self.read_string()
        return int.from_bytes(buf, byteorder="big", signed=False)
