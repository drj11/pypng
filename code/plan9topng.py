#!/usr/bin/env python
# $Rev$
# $URL$

# Imported from //depot/prj/plan9topam/master/code/plan9topam.py#4 on
# 2009-06-15.

"""Command line tool to convert from Plan 9 image format to PNG format.

Plan 9 image format description:
https://plan9.io/magic/man2html/6/image
"""

# http://www.python.org/doc/2.3.5/lib/module-itertools.html
import itertools
# http://www.python.org/doc/2.3.5/lib/module-re.html
import re
# http://www.python.org/doc/2.3.5/lib/module-sys.html
import sys

import png


class Error(Exception):
    """Some sort of Plan 9 image error."""


def block(s, n):
    return zip(* [iter(s)] * n)


def convert(f, output=png.binary_stdout()):
    """Convert Plan 9 file to PNG format.  Works with either uncompressed
    or compressed files.
    """

    r = f.read(11)
    if r == b'compressed\n':
        info, fd = decompress(f)
    else:
        # Since Python 3, there is a good chance that this path
        # doesn't work.
        info, fd = glue(f, r)

    write_png(output, info, fd)


def glue(f, r):
    """Return (metadata, stream) pair where `r` is the initial portion of
    the metadata that has already been read from the stream `f`.
    """

    r = r + f.read(60 - len(r))
    return (r, f)


def meta(r):
    """Convert 60 byte bytestring `r`, the metadata from an image file.
    Returns a 5-tuple (*chan*,*minx*,*miny*,*limx*,*limy*).
    5-tuples may settle into lists in transit.

    As per https://plan9.io/magic/man2html/6/font the metadata
    comprises 5 words separated by blanks.  As it happens each word starts
    at an index that is a multiple of 12, but this routine does not care
    about that."""

    r = r.split()
    # :todo: raise FormatError
    if 5 != len(r):
        raise Error("Expected 5 space-separated words in metadata")
    r = [r[0]] + [int(x) for x in r[1:]]
    return r


def bitdepthof(pixel):
    """Return the bitdepth for a Plan9 pixel format string."""

    maxd = 0
    for c in re.findall(rb'[a-z]\d*', pixel):
        if c[0] != 'x':
            maxd = max(maxd, int(c[1:]))
    return maxd


def maxvalof(pixel):
    """Return the netpbm MAXVAL for a Plan9 pixel format string."""

    bitdepth = bitdepthof(pixel)
    return (2 ** bitdepth) - 1


def pixmeta(metadata, f):
    """
    Convert (uncompressed) Plan 9 image file to pair of (*metadata*, *pixels*).
    This is intended to be used by PyPNG format.
    *metadata* (the return value) is the metadata returned in a dictionary,
    *pixels* is an iterator that yields each row in
    boxed row flat pixel format.

    `f`, the input file, should be cued up to the start of the image data.
    """

    chan, minx, miny, limx, limy = metadata
    rows = limy - miny
    width = limx - minx
    nchans = len(re.findall(b'[a-wyz]', chan))
    alpha = b'a' in chan
    # Iverson's convention for the win!
    ncolour = nchans - alpha
    greyscale = ncolour == 1
    bitdepth = bitdepthof(chan)
    maxval = 2**bitdepth - 1
    # PNG style metadata
    meta = dict(size=(width, rows), bitdepth=bitdepthof(chan),
                greyscale=greyscale, alpha=alpha, planes=nchans)

    return map(
        lambda x: itertools.chain(*x),
        block(unpack(f, rows, width, chan, maxval), width)), meta


def write_png(out, info, f):
    """Convert to PNG format.
    `info` should be a Plan9 5-tuple;
    `f` the input file (see :meth:`pixmeta`).
    """

    pixels, infodict = pixmeta(info, f)
    p = png.Writer(**infodict)
    p.write(out, pixels)


def unpack(f, rows, width, chan, maxval):
    """Unpack `f` into pixels.
    `chan` describes the pixel format using
    the Plan9 syntax ("k8", "r8g8b8", and so on).
    Assumes the pixel format has a total channel bit depth
    that is either a multiple or a divisor of 8
    (the Plan9 image specification requires this).
    `f` should be an iterator that returns blocks of input such that
    each block contains a whole number of pixels.
    The return value is an iterator that yields each pixel as an n-tuple.
    """

    def mask(w):
        """An integer, to be used as a mask, with bottom `w` bits set to 1."""

        return (1 << w) - 1

    def deblock(f, depth, width):
        """A "packer" used to convert multiple bytes into single pixels.
        `depth` is the pixel depth in bits (>= 8), `width` is the row width in
        pixels.
        """

        w = depth // 8
        i = 0
        for block in f:
            for i in range(len(block) // w):
                p = block[w * i: w * (i + 1)]
                i += w
                # Convert little-endian p to integer x
                x = 0
                s = 1   # scale
                for j in p:
                    x += s * j
                    s <<= 8
                yield x

    def bitfunge(f, depth, width):
        """A "packer" used to convert single bytes into multiple pixels.
        Depth is the pixel depth (< 8), width is the row width in pixels.
        """

        for block in f:
            col = 0
            for x in block:
                for j in range(8 / depth):
                    yield x >> (8 - depth)
                    col += 1
                    if col == width:
                        # A row-end forces a new byte even if
                        # we haven't consumed all of the current byte.
                        # Effectively rows are bit-padded to make
                        # a whole number of bytes.
                        col = 0
                        break
                    x <<= depth

    # number of bits in each channel
    bits = [int(d) for d in re.findall(rb'\d+', chan)]
    # colr of each channel
    # (r, g, b, k for actual colours, and
    # a, m, x for alpha, map-index, and unused)
    colr = re.findall(b'[a-z]', chan)

    depth = sum(bits)

    # Select a "packer" that either:
    # - gathers multiple bytes into a single pixel (for depth >= 8); or,
    # - splits bytes into several pixels (for depth < 8).
    if depth >= 8:
        assert depth % 8 == 0
        packer = deblock
    else:
        assert 8 % depth == 0
        packer = bitfunge

    for x in packer(f, depth, width):
        # x is the pixel as an unsigned integer
        o = []
        # This is a bit yucky.
        # Extract each channel from the _most_ significant part of x.
        for b, col in zip(bits, colr):
            v = (x >> (depth - b)) & mask(b)
            x <<= b
            if col != 'x':
                # scale to maxval
                v = v * float(maxval) / mask(b)
                v = int(v + 0.5)
                o.append(v)
        yield o


def decompress(f):
    """Decompress a Plan 9 image file.  Assumes f is already cued past the
    initial 'compressed\n' string.
    """

    r = meta(f.read(60))
    return r, decomprest(f, r[4])


def decomprest(f, rows):
    """Iterator that decompresses the rest of a file once the metadata
    have been consumed."""

    row = 0
    while row < rows:
        row, o = deblock(f)
        yield o


def deblock(f):
    """Decompress a single block from a compressed Plan 9 image file.
    Each block starts with 2 decimal strings of 12 bytes each.  Yields a
    sequence of (row, data) pairs where row is the total number of rows
    processed according to the file format and data is the decompressed
    data for a set of rows."""

    row = int(f.read(12))
    size = int(f.read(12))
    if not (0 <= size <= 6000):
        raise Error('block has invalid size; not a Plan 9 image file?')

    # Since each block is at most 6000 bytes we may as well read it all in
    # one go.
    d = f.read(size)
    i = 0
    o = []

    while i < size:
        x = d[i]
        i += 1
        if x & 0x80:
            x = (x & 0x7f) + 1
            lit = d[i: i + x]
            i += x
            o.extend(lit)
            continue
        # x's high-order bit is 0
        length = (x >> 2) + 3
        # Offset is made from bottom 2 bits of x and 8 bits of next byte.
        # https://plan9.io/magic/man2html/6/font doesn't say
        # whether x's 2 bits are most significant or least significant.
        # But it is clear from inspecting a random file,
        # http://plan9.bell-labs.com/sources/plan9/sys/games/lib/sokoban/images/cargo.bit
        # that x's 2 bits are most significant.
        offset = (x & 3) << 8
        offset |= d[i]
        i += 1
        # Note: complement operator neatly maps (0 to 1023) to (-1 to
        # -1024).  Adding len(o) gives a (non-negative) offset into o from
        # which to start indexing.
        offset = ~offset + len(o)
        if offset < 0:
            raise Error('byte offset indexes off the begininning of '
                        'the output buffer; not a Plan 9 image file?')
        for j in range(length):
            o.append(o[offset + j])
    return row, bytes(o)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(sys.argv) <= 1:
        arg = "-"
    else:
        arg = argv[1]
    return convert(png.cli_open(arg))


if __name__ == '__main__':
    sys.exit(main())
