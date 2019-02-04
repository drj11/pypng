# minpng.py

import struct
import zlib

"""
minpng.py

MinPNG (minimal PNG) is the antidote to PyPNG.
Where PyPNG is several thousand lines and
can write and read all PNG formats,
MinPNG is two-dozen lines that writes
an 8-bit greyscale PNG and does nothing else.
"""


def rows_to_png(out, rows, size):
    """Write to the binary file `out` a single channel 8-bit PNG.
    `rows` should yield each row in turn;
    `size` should be the tuple of (width, height) in pixels.
    """

    # Write out PNG signature.
    out.write(bytearray([137, 80, 78, 71, 13, 10, 26, 10]))
    # Write out PNG header chunk.
    header = struct.pack(">2LBBBBB", size[0], size[1], 8, 0, 0, 0, 0)
    write_chunk(out, b"IHDR", header)

    bs = bytearray()
    for row in rows:
        bs.append(0)
        bs.extend(row)
    write_chunk(out, b"IDAT", zlib.compress(bs))

    write_chunk(out, b"IEND", bytearray())


def write_chunk(out, chunk_type, data):
    assert 4 == len(chunk_type)
    out.write(struct.pack(">L", len(data)))
    out.write(chunk_type)
    out.write(data)
    checksum = zlib.crc32(chunk_type)
    checksum = zlib.crc32(data, checksum)
    out.write(struct.pack(">L", checksum))
