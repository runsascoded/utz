from io import TextIOWrapper

import struct
from contextlib import contextmanager
from gzip import GzipFile


class DeterministicGzipFile(GzipFile):
    """
    A GzipFile subclass that writes deterministic output by:
    1. Setting fixed metadata values in the header
    2. Using a consistent modification time
    3. Not including the filename in the header
    """
    def _write_gzip_header(self, compresslevel):
        self.fileobj.write(b'\037\213')             # Magic number
        self.fileobj.write(b'\010')                 # Compression method
        fname = b''
        flags = 0
        self.fileobj.write(chr(flags).encode('latin-1'))
        mtime = 0  # Using 0 as a fixed modification time
        self.fileobj.write(struct.pack("<L", mtime))
        # Set extra flags based on compression level:
        # 2 -> maximum compression
        # 4 -> fastest algorithm
        xfl = 2 if compresslevel >= 9 else (4 if compresslevel == 1 else 0)
        self.fileobj.write(bytes([xfl]))
        self.fileobj.write(b'\377')                 # OS (unknown)
        if fname:
            self.fileobj.write(fname + b'\000')


@contextmanager
def deterministic_gzip_open(
    path: str,
    mode: str,
    compression_level: int = 9,
    encoding: str = 'utf-8',
):
    """
    Opens a gzip file with deterministic output settings.
    Note: The file object must be used within a context manager.
    """
    gzip_file = None
    raw_file = None
    try:
        raw_file = open(path, "wb")
        gzip_file = DeterministicGzipFile(
            fileobj=raw_file,
            mode=mode,
            compresslevel=compression_level,
        )
        # Wrap in TextIOWrapper if text mode is requested
        if 'b' not in mode:
            gzip_file = TextIOWrapper(gzip_file, encoding=encoding)
        yield gzip_file
    finally:
        if gzip_file:
            gzip_file.close()
        if raw_file:
            raw_file.close()
