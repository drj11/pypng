#!/usr/bin/env python

from __future__ import print_function

# png.py - PNG encoder/decoder in pure Python
#
# Copyright (C) 2006 Johann C. Rocholl <johann@browsershots.org>
# Portions Copyright (C) 2009 David Jones <drj@pobox.com>
# And probably portions Copyright (C) 2006 Nicko van Someren <nicko@nicko.org>
#
# Original concept by Johann C. Rocholl.
#
# LICENCE (MIT)
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Pure Python PNG Reader/Writer

This Python module implements support for PNG images (see PNG
specification at http://www.w3.org/TR/2003/REC-PNG-20031110/ ). It reads
and writes PNG files with all allowable bit depths
(1/2/4/8/16/24/32/48/64 bits per pixel) and colour combinations:
greyscale (1/2/4/8/16 bit); RGB, RGBA, LA (greyscale with alpha) with
8/16 bits per channel; colour mapped images (1/2/4/8 bit).
Adam7 interlacing is supported for reading and
writing.  A number of optional chunks can be specified (when writing)
and understood (when reading): ``tRNS``, ``bKGD``, ``gAMA``.

For help, type ``import png; help(png)`` in your python interpreter.

A good place to start is the :class:`Reader` and :class:`Writer`
classes.

Requires Python 3.4 or higher (or Python 2.6 or higher).
Installation is trivial,
but see the ``README.txt`` file (with the source distribution) for details.

The package also comes with command line utilities that convert
`Netpbm <http://netpbm.sourceforge.net/>`_ PNM files to PNG,
and the reverse conversion from PNG to PNM,
and some simple PNG manipulations.

A note on spelling and terminology
----------------------------------

Generally British English spelling is used in the documentation.  So
that's "greyscale" and "colour".  This not only matches the author's
native language, it's also used by the PNG specification.

The major colour models supported by PNG (and hence by PyPNG) are:
greyscale, RGB, greyscale--alpha, RGB--alpha.  These are sometimes
referred to using the abbreviations: L, RGB, LA, RGBA.  In this case
each letter abbreviates a single channel: *L* is for Luminance or Luma
or Lightness which is the channel used in greyscale images; *R*, *G*,
*B* stand for Red, Green, Blue, the components of a colour image; *A*
stands for Alpha, the opacity channel (used for transparency effects,
but higher values are more opaque, so it makes sense to call it
opacity).

A note on formats
-----------------

When getting pixel data out of this module (reading) and presenting
data to this module (writing) there are a number of ways the data could
be represented as a Python value.  Generally this module uses one of
three formats called "flat row flat pixel", "boxed row flat pixel", and
"boxed row boxed pixel".  Basically the concern is whether each pixel
and each row comes in its own little tuple (box), or not.

Consider an image that is 3 pixels wide by 2 pixels high, and each pixel
has RGB components:

Boxed row flat pixel::

  list([R,G,B, R,G,B, R,G,B],
       [R,G,B, R,G,B, R,G,B])

Each row appears as its own list, but the pixels are flattened so
that three values for one pixel simply follow the three values for
the previous pixel.  This is the most common format used, because it
provides a good compromise between space and convenience.  PyPNG regards
itself as at liberty to replace any sequence type with any sufficiently
compatible other sequence type; in practice each row is an array (from
the array module), and the outer list is sometimes an iterator rather
than an explicit list (so that streaming is possible).

Flat row flat pixel::

  [R,G,B, R,G,B, R,G,B,
   R,G,B, R,G,B, R,G,B]

The entire image is one single giant sequence of colour values.
Generally an array will be used (to save space), not a list.

Boxed row boxed pixel::

  list([ (R,G,B), (R,G,B), (R,G,B) ],
       [ (R,G,B), (R,G,B), (R,G,B) ])

Each row appears in its own list, but each pixel also appears in its own
tuple.  A serious memory burn in Python.

In all cases the top row comes first, and for each row the pixels are
ordered from left-to-right.  Within a pixel the values appear in the
order, R-G-B-A (or L-A for greyscale--alpha).

There is a fourth format, mentioned because it is used internally,
is close to what lies inside a PNG file itself, and has some support
from the public API.  This format is called packed.  When packed,
each row is a sequence of bytes (integers from 0 to 255), just as
it is before PNG scanline filtering is applied.  When the bit depth
is 8 this is essentially the same as boxed row flat pixel; when the
bit depth is less than 8, several pixels are packed into each byte;
when the bit depth is 16 (the only value more than 8 that is supported
by the PNG image format) each pixel value is decomposed into 2 bytes
(and `packed` is a misnomer).  This format is used by the
:meth:`Writer.write_packed` method.  It isn't usually a convenient
format, but may be just right if the source data for the PNG image
comes from something that uses a similar format (for example, 1-bit
BMPs, or another PNG file).

And now, my famous members
--------------------------
"""

__version__ = "0.0.19"

import collections
import io   # For io.BytesIO
import itertools
import math
# http://www.python.org/doc/2.4.4/lib/module-operator.html
import operator
import re
import struct
import sys
# http://www.python.org/doc/2.4.4/lib/module-warnings.html
import warnings
import zlib

from array import array

try:
    # `cpngfilters` is a Cython module: it must be compiled by
    # Cython for this import to work.
    # If this import does work, then it overrides pure-python
    # filtering functions defined later in this file (see `class
    # pngfilters`).
    import cpngfilters as pngfilters
except ImportError:
    pass


__all__ = ['Image', 'Reader', 'Writer', 'write_chunks', 'from_array']


# The PNG signature.
# http://www.w3.org/TR/PNG/#5PNG-file-signature
signature = struct.pack('8B', 137, 80, 78, 71, 13, 10, 26, 10)

# The xstart, ystart, xstep, ystep for the Adam7 interlace passes.
adam7 = ((0, 0, 8, 8),
         (4, 0, 8, 8),
         (0, 4, 4, 8),
         (2, 0, 4, 4),
         (0, 2, 2, 4),
         (1, 0, 2, 2),
         (0, 1, 1, 2))


def adam7_generate(width, height):
    """
    Generate the coordinates for the reduced scanlines
    of an Adam7 interlaced image
    of size `width` by `height` pixels.

    Yields a generator for each pass,
    and each pass generator yields a series of (x, y, xstep) triples,
    each one identifying a reduced scanline consisting of
    pixels starting at (x, y) and taking every xstep pixel to the right.
    """

    for xstart, ystart, xstep, ystep in adam7:
        if xstart >= width:
            continue
        yield ((xstart, y, xstep) for y in range(ystart, height, ystep))


# Models the 'pHYs' chunk (used by the Reader)
Resolution = collections.namedtuple('_Resolution', 'x y unit_is_meter')


def group(s, n):
    # See http://www.python.org/doc/2.6/library/functions.html#zip
    return list(zip(* [iter(s)] * n))


def isarray(x):
    return isinstance(x, array)


def check_palette(palette):
    """
    Check a palette argument (to the :class:`Writer` class) for validity.
    Returns the palette as a list if okay;
    raises an exception otherwise.
    """

    # None is the default and is allowed.
    if palette is None:
        return None

    p = list(palette)
    if not (0 < len(p) <= 256):
        raise ProtocolError(
            "a palette must have between 1 and 256 entries,"
            " see https://www.w3.org/TR/PNG/#11PLTE")
    seen_triple = False
    for i, t in enumerate(p):
        if len(t) not in (3, 4):
            raise ProtocolError(
                "palette entry %d: entries must be 3- or 4-tuples." % i)
        if len(t) == 3:
            seen_triple = True
        if seen_triple and len(t) == 4:
            raise ProtocolError(
                "palette entry %d: all 4-tuples must precede all 3-tuples" % i)
        for x in t:
            if int(x) != x or not(0 <= x <= 255):
                raise ProtocolError(
                    "palette entry %d: "
                    "values must be integer: 0 <= x <= 255" % i)
    return p


def check_sizes(size, width, height):
    """
    Check that these arguments, if supplied, are consistent.
    Return a (width, height) pair.
    """

    if not size:
        return width, height

    if len(size) != 2:
        raise ValueError(
            "size argument should be a pair (width, height)")
    if width is not None and width != size[0]:
        raise ValueError(
            "size[0] (%r) and width (%r) should match when both are used."
            % (size[0], width))
    if height is not None and height != size[1]:
        raise ValueError(
            "size[1] (%r) and height (%r) should match when both are used."
            % (size[1], height))
    return size


def check_color(c, greyscale, which):
    """
    Checks that a colour argument for transparent or background options
    is the right form.
    Returns the colour
    (which, if it's a bare integer, is "corrected" to a 1-tuple).
    """

    if c is None:
        return c
    if greyscale:
        try:
            len(c)
        except TypeError:
            c = (c,)
        if len(c) != 1:
            raise ValueError("%s for greyscale must be 1-tuple" % which)
        if not is_natural(c[0]):
            raise ValueError(
                "%s colour for greyscale must be integer" % which)
    else:
        if not (len(c) == 3 and
                is_natural(c[0]) and
                is_natural(c[1]) and
                is_natural(c[2])):
            raise ValueError(
                "%s colour must be a triple of integers" % which)
    return c


class Error(Exception):
    def __str__(self):
        return self.__class__.__name__ + ': ' + ' '.join(self.args)


class FormatError(Error):
    """
    Problem with input file format.
    In other words, PNG file does not conform to
    the specification in some way and is invalid.
    """


class ProtocolError(Error):
    """
    Problem with the way the programming interface has been used,
    or the data presented to it.
    """


class ChunkError(FormatError):
    pass


class Writer:
    """
    PNG encoder in pure Python.
    """

    def __init__(self, width=None, height=None,
                 size=None,
                 greyscale=False,
                 alpha=False,
                 bitdepth=8,
                 palette=None,
                 transparent=None,
                 background=None,
                 gamma=None,
                 compression=None,
                 interlace=False,
                 bytes_per_sample=None,     # deprecated
                 planes=None,
                 colormap=None,
                 maxval=None,
                 chunk_limit=2**20,
                 x_pixels_per_unit=None,
                 y_pixels_per_unit=None,
                 unit_is_meter=False):
        """
        Create a PNG encoder object.

        Arguments:

        width, height
          Image size in pixels, as two separate arguments.
        size
          Image size (w,h) in pixels, as single argument.
        greyscale
          Input data is greyscale, not RGB.
        alpha
          Input data has alpha channel (RGBA or LA).
        bitdepth
          Bit depth: from 1 to 16 (for each channel).
        palette
          Create a palette for a colour mapped image (colour type 3).
        transparent
          Specify a transparent colour (create a ``tRNS`` chunk).
        background
          Specify a default background colour (create a ``bKGD`` chunk).
        gamma
          Specify a gamma value (create a ``gAMA`` chunk).
        compression
          zlib compression level: 0 (none) to 9 (more compressed);
          default: -1 or None.
        interlace
          Create an interlaced image.
        chunk_limit
          Write multiple ``IDAT`` chunks to save memory.
        x_pixels_per_unit
          Number of pixels a unit along the x axis (write a
          `pHYs` chunk).
        y_pixels_per_unit
          Number of pixels a unit along the y axis (write a
          `pHYs` chunk). Along with `x_pixel_unit`, this gives
          the pixel size ratio.
        unit_is_meter
          `True` to indicate that the unit (for the `pHYs`
          chunk) is metre.

        The image size (in pixels) can be specified either by using the
        `width` and `height` arguments, or with the single `size`
        argument.
        If `size` is used it should be a pair (*width*, *height*).

        `greyscale` and `alpha` are booleans that specify
        whether an image is greyscale (or colour), and
        whether it has an alpha channel (or not).

        `bitdepth` specifies the bit depth of the source pixel values.
        Each channel may have a different bit depth.
        Each source pixel must have values that are
        an integer between 0 and ``2**bitdepth-1``, where
        `bitdepth` is the bit depth for the corresponding channel.
        For example, 8-bit images have values between 0 and 255.
        PNG only stores images with bit depths of
        1,2,4,8, or 16 (the same for all channels).
        When `bitdepth` is not one of these values or where
        channels have different bit depths,
        the next highest valid bit depth is selected,
        and an ``sBIT`` (significant bits) chunk is generated
        that specifies the original precision of the source image.
        In this case the supplied pixel values will be rescaled to
        fit the range of the selected bit depth.

        The PNG file format supports many bit depth / colour model
        combinations, but not all.
        The details are somewhat arcane
        (refer to the PNG specification for full details).
        Briefly:
        Bit depths < 8 (1,2,4) are only allowed with greyscale and
        colour mapped images;
        colour mapped images cannot have bit depth 16.

        For colour mapped images
        (in other words, when the `palette` argument is specified)
        the `bitdepth` argument must match one of
        the valid PNG bit depths: 1, 2, 4, or 8.
        (It is valid to have a PNG image with a palette and
        an ``sBIT`` chunk, but the meaning is slightly different;
        it would be awkward to use the `bitdepth` argument for this.)

        The `palette` option, when specified,
        causes a colour mapped image to be created:
        the PNG colour type is set to 3;
        `greyscale` must not be set; `alpha` must not be set;
        `transparent` must not be set.
        The bit depth must be 1,2,4, or 8.
        When a colour mapped image is created,
        the pixel values are palette indexes and
        the `bitdepth` argument specifies the size of these indexes
        (not the size of the colour values in the palette).

        The palette argument value should be a sequence of 3- or
        4-tuples.
        3-tuples specify RGB palette entries;
        4-tuples specify RGBA palette entries.
        All the 4-tuples (if present) must come before all the 3-tuples.
        A ``PLTE`` chunk is created;
        if there are 4-tuples then a ``tRNS`` chunk is created as well.
        The ``PLTE`` chunk will contain all the RGB triples in the same
        sequence;
        the ``tRNS`` chunk will contain the alpha channel for
        all the 4-tuples, in the same sequence.
        Palette entries are always 8-bit.

        If specified, the `transparent` and `background` parameters must be
        a tuple with one element for each channel in the image.
        Either a 3-tuple of integer (RGB) values for a colour image, or
        a 1-tuple of a single integer for a greyscale image.

        If specified, the `gamma` parameter must be a positive number
        (generally, a `float`).
        A ``gAMA`` chunk will be created.
        Note that this will not change the values of the pixels as
        they appear in the PNG file,
        they are assumed to have already
        been converted appropriately for the gamma specified.

        The `compression` argument specifies the compression level to
        be used by the ``zlib`` module.
        Values from 1 to 9 (highest) specify compression.
        0 means no compression.
        -1 and ``None`` both mean that the ``zlib`` module uses
        the default level of compession (which is generally acceptable).

        If `interlace` is true then an interlaced image is created
        (using PNG's so far only interace method, *Adam7*).
        This does not affect how the pixels should be passed in,
        rather it changes how they are arranged into the PNG file.
        On slow connexions interlaced images can be
        partially decoded by the browser to give
        a rough view of the image that is
        successively refined as more image data appears.

        .. note ::

          Enabling the `interlace` option requires the entire image
          to be processed in working memory.

        `chunk_limit` is used to limit the amount of memory used whilst
        compressing the image.
        In order to avoid using large amounts of memory,
        multiple ``IDAT`` chunks may be created.
        """

        # At the moment the `planes` argument is ignored;
        # its purpose is to act as a dummy so that
        # ``Writer(x, y, **info)`` works, where `info` is a dictionary
        # returned by Reader.read and friends.
        # Ditto for `colormap`.

        width, height = check_sizes(size, width, height)
        del size

        if not is_natural(width) or not is_natural(height):
            raise ProtocolError("width and height must be integers")
        if width <= 0 or height <= 0:
            raise ProtocolError("width and height must be greater than zero")
        # http://www.w3.org/TR/PNG/#7Integers-and-byte-order
        if width > 2 ** 31 - 1 or height > 2 ** 31 - 1:
            raise ProtocolError("width and height cannot exceed 2**31-1")

        if alpha and transparent is not None:
            raise ValueError(
                "transparent colour not allowed with alpha channel")

        if bytes_per_sample is not None:
            warnings.warn('please use bitdepth instead of bytes_per_sample',
                          DeprecationWarning)
            if bytes_per_sample not in (0.125, 0.25, 0.5, 1, 2):
                raise ValueError(
                    "bytes per sample must be .125, .25, .5, 1, or 2")
            bitdepth = int(8 * bytes_per_sample)
        del bytes_per_sample
        # bitdepth is either single integer, or tuple of integers.
        # Convert to tuple.
        try:
            len(bitdepth)
        except TypeError:
            bitdepth = (bitdepth, )
        for b in bitdepth:
            valid = is_natural(b) and 1 <= b <= 16
            if not valid:
                raise ValueError(
                    "each bitdepth %r must be a positive integer <= 16" %
                    (bitdepth,))

        # Calculate channels, and
        # expand bitdepth to be one element per channel.
        palette = check_palette(palette)
        alpha = bool(alpha)
        colormap = bool(palette)
        greyscale = bool(greyscale)
        color_planes = (3, 1)[greyscale or colormap]
        planes = color_planes + alpha
        if len(bitdepth) == 1:
            bitdepth *= planes

        bitdepth, self.rescale = check_bitdepth_rescale(
                palette,
                bitdepth,
                transparent, alpha, greyscale)

        # These are assertions, because above logic should have
        # corrected or raised all problematic cases.
        if bitdepth < 8:
            assert greyscale or palette
            assert not alpha
        if bitdepth > 8:
            assert not palette

        transparent = check_color(transparent, greyscale, 'transparent')
        background = check_color(background, greyscale, 'background')

        # It's important that the true boolean values
        # (greyscale, alpha, colormap, interlace) are converted
        # to bool because Iverson's convention is relied upon later on.
        self.width = width
        self.height = height
        self.transparent = transparent
        self.background = background
        self.gamma = gamma
        self.greyscale = greyscale
        self.alpha = alpha
        self.colormap = colormap
        self.bitdepth = int(bitdepth)
        self.compression = compression
        self.chunk_limit = chunk_limit
        self.interlace = bool(interlace)
        self.palette = palette
        self.x_pixels_per_unit = x_pixels_per_unit
        self.y_pixels_per_unit = y_pixels_per_unit
        self.unit_is_meter = bool(unit_is_meter)

        self.color_type = (4 * self.alpha +
                           2 * (not greyscale) +
                           1 * self.colormap)
        assert self.color_type in (0, 2, 3, 4, 6)

        self.color_planes = color_planes
        self.planes = planes
        # :todo: fix for bitdepth < 8
        self.psize = (self.bitdepth / 8) * self.planes

    def write(self, outfile, rows):
        """
        Write a PNG image to the output file.
        `rows` should be an iterable that yields each row
        in boxed row flat pixel format.
        The rows should be the rows of the original image,
        so there should be ``self.height`` rows of
        ``self.width * self.planes`` values.
        If `interlace` is specified (when creating the instance),
        then an interlaced PNG file will be written.
        Supply the rows in the normal image order;
        the interlacing is carried out internally.

        .. note ::

          Interlacing requires the entire image to be in working memory.
        """

        # Values per row
        vpr = self.width * self.planes

        def check_rows(rows):
            """
            Yield each row in rows,
            but check each row first (for correct width).
            """
            for i, row in enumerate(rows):
                try:
                    wrong_length = len(row) != vpr
                except TypeError:
                    # When using an itertools.ichain object or
                    # other generator not supporting __len__,
                    # we set this to False to skip the check.
                    wrong_length = False
                if wrong_length:
                    # Note: row numbers start at 0.
                    raise ProtocolError(
                        "Expected %d values but got %d value, in row %d" %
                        (vpr, len(row), i))
                yield row

        if self.interlace:
            fmt = 'BH'[self.bitdepth > 8]
            a = array(fmt, itertools.chain(*check_rows(rows)))
            return self.write_array(outfile, a)

        nrows = self.write_passes(outfile, check_rows(rows))
        if nrows != self.height:
            raise ValueError(
                "rows supplied (%d) does not match height (%d)" %
                (nrows, self.height))

    def write_passes(self, outfile, rows):
        """
        Write a PNG image to the output file.

        Most users are expected to find the :meth:`write` or
        :meth:`write_array` method more convenient.

        The rows should be given to this method in the order that
        they appear in the output file.
        For straightlaced images, this is the usual top to bottom ordering.
        For interlaced images the rows should have been interlaced before
        passing them to this function.

        `rows` should be an iterable that yields each row.
        The rows should be in boxed row flat pixel format.
        """

        # Ensure rows are scaled (to 4-/8-/16-bit),
        # and packed into bytes.

        if self.rescale:
            rows = rescale_rows(rows, self.rescale)

        if self.bitdepth < 8:
            rows = pack_rows(rows, self.bitdepth)
        elif self.bitdepth == 16:
            rows = unpack_rows(rows)

        return self.write_packed(outfile, rows)

    def write_packed(self, outfile, rows):
        """
        Write PNG file to `outfile`.
        `rows` should be in boxed row packed format.
        Each row should be a sequence of packed bytes.

        The rows have a filter byte prefixed and
        are then compressed into one or more IDAT chunks.
        They are not processed any further,
        so if bitdepth is other than 1, 2, 4, 8, 16,
        the pixel values should have been scaled
        before passing them to this method.

        This method does work for interlaced images but it is best avoided.
        For interlaced images, the rows should be
        presented in the order that they appear in the file.
        """

        self.write_preamble(outfile)

        # http://www.w3.org/TR/PNG/#11IDAT
        if self.compression is not None:
            compressor = zlib.compressobj(self.compression)
        else:
            compressor = zlib.compressobj()

        # data accumulates bytes to be compressed for the IDAT chunk;
        # it's compressed when sufficiently large.
        data = bytearray()

        for i, row in enumerate(rows):
            # Add "None" filter type.
            # Currently, it's essential that this filter type be used
            # for every scanline as
            # we do not mark the first row of a reduced pass image;
            # that means we could accidentally compute
            # the wrong filtered scanline if we used
            # "up", "average", or "paeth" on such a line.
            data.append(0)
            data.extend(row)
            if len(data) > self.chunk_limit:
                # :todo: bytes() only necessary in Python 2
                compressed = compressor.compress(bytes(data))
                if len(compressed):
                    write_chunk(outfile, b'IDAT', compressed)
                data = bytearray()

        compressed = compressor.compress(bytes(data))
        flushed = compressor.flush()
        if len(compressed) or len(flushed):
            write_chunk(outfile, b'IDAT', compressed + flushed)
        # http://www.w3.org/TR/PNG/#11IEND
        write_chunk(outfile, b'IEND')
        return i + 1

    def write_preamble(self, outfile):
        # http://www.w3.org/TR/PNG/#5PNG-file-signature
        outfile.write(signature)

        # http://www.w3.org/TR/PNG/#11IHDR
        write_chunk(outfile, b'IHDR',
                    struct.pack("!2I5B", self.width, self.height,
                                self.bitdepth, self.color_type,
                                0, 0, self.interlace))

        # See :chunk:order
        # http://www.w3.org/TR/PNG/#11gAMA
        if self.gamma is not None:
            write_chunk(outfile, b'gAMA',
                        struct.pack("!L", int(round(self.gamma * 1e5))))

        # See :chunk:order
        # http://www.w3.org/TR/PNG/#11sBIT
        if self.rescale:
            write_chunk(
                outfile, b'sBIT',
                struct.pack('%dB' % self.planes,
                            * [s[0] for s in self.rescale]))

        # :chunk:order: Without a palette (PLTE chunk),
        # ordering is relatively relaxed.
        # With one, gAMA chunk must precede PLTE chunk
        # which must precede tRNS and bKGD.
        # See http://www.w3.org/TR/PNG/#5ChunkOrdering
        if self.palette:
            p, t = make_palette_chunks(self.palette)
            write_chunk(outfile, b'PLTE', p)
            if t:
                # tRNS chunk is optional;
                # Only needed if palette entries have alpha.
                write_chunk(outfile, b'tRNS', t)

        # http://www.w3.org/TR/PNG/#11tRNS
        if self.transparent is not None:
            if self.greyscale:
                fmt = "!1H"
            else:
                fmt = "!3H"
            write_chunk(outfile, b'tRNS',
                        struct.pack(fmt, *self.transparent))

        # http://www.w3.org/TR/PNG/#11bKGD
        if self.background is not None:
            if self.greyscale:
                fmt = "!1H"
            else:
                fmt = "!3H"
            write_chunk(outfile, b'bKGD',
                        struct.pack(fmt, *self.background))

        # http://www.w3.org/TR/PNG/#11pHYs
        if (self.x_pixels_per_unit is not None and
                self.y_pixels_per_unit is not None):
            tup = (self.x_pixels_per_unit,
                   self.y_pixels_per_unit,
                   int(self.unit_is_meter))
            write_chunk(outfile, b'pHYs', struct.pack("!LLB", *tup))

    def write_array(self, outfile, pixels):
        """
        Write an array in flat row flat pixel format as
        a PNG file on the output file.
        See also :meth:`write` method.
        """

        if self.interlace:
            if type(pixels) != array:
                # Coerce to array type
                fmt = 'BH'[self.bitdepth > 8]
                pixels = array(fmt, pixels)
            self.write_passes(outfile, self.array_scanlines_interlace(pixels))
        else:
            self.write_passes(outfile, self.array_scanlines(pixels))

    def array_scanlines(self, pixels):
        """
        Generates boxed rows (flat pixels) from flat rows (flat pixels)
        in an array.
        """

        # Values per row
        vpr = self.width * self.planes
        stop = 0
        for y in range(self.height):
            start = stop
            stop = start + vpr
            yield pixels[start:stop]

    def array_scanlines_interlace(self, pixels):
        """
        Generator for interlaced scanlines from an array.
        `pixels` is the full source image in flat row flat pixel format.
        The generator yields each scanline of the reduced passes in turn,
        in boxed row flat pixel format.
        """

        # http://www.w3.org/TR/PNG/#8InterlaceMethods
        # Array type.
        fmt = 'BH'[self.bitdepth > 8]
        # Value per row
        vpr = self.width * self.planes

        # Each iteration generates a scanline starting at (x, y)
        # and consisting of every xstep pixels.
        for lines in adam7_generate(self.width, self.height):
            for x, y, xstep in lines:
                # Pixels per row (of reduced image)
                ppr = int(math.ceil((self.width - x) / float(xstep)))
                # Values per row (of reduced image)
                reduced_row_len = ppr * self.planes
                if xstep == 1:
                    # Easy case: line is a simple slice.
                    offset = y * vpr
                    yield pixels[offset: offset + vpr]
                    continue
                # We have to step by xstep,
                # which we can do one plane at a time
                # using the step in Python slices.
                row = array(fmt)
                # There's no easier way to set the length of an array
                row.extend(pixels[0:reduced_row_len])
                offset = y * vpr + x * self.planes
                end_offset = (y + 1) * vpr
                skip = self.planes * xstep
                for i in range(self.planes):
                    row[i::self.planes] = \
                        pixels[offset + i: end_offset: skip]
                yield row


def write_chunk(outfile, tag, data=b''):
    """
    Write a PNG chunk to the output file, including length and
    checksum.
    """

    data = bytes(data)
    # http://www.w3.org/TR/PNG/#5Chunk-layout
    outfile.write(struct.pack("!I", len(data)))
    outfile.write(tag)
    outfile.write(data)
    checksum = zlib.crc32(tag)
    checksum = zlib.crc32(data, checksum)
    checksum &= 2 ** 32 - 1
    outfile.write(struct.pack("!I", checksum))


def write_chunks(out, chunks):
    """Create a PNG file by writing out the chunks."""

    out.write(signature)
    for chunk in chunks:
        write_chunk(out, *chunk)


def rescale_rows(rows, rescale):
    """
    Take each row in rows (an iterator) and yield
    a fresh row with the pixels scaled according to
    the rescale parameters in the list `rescale`.
    Each element of `rescale` is a tuple of
    (source_bitdepth, target_bitdepth),
    with one element per channel.
    """

    # One factor for each channel
    fs = [float(2 ** s[1] - 1)/float(2 ** s[0] - 1)
          for s in rescale]

    # Assume all target_bitdepths are the same
    target_bitdepths = set(s[1] for s in rescale)
    assert len(target_bitdepths) == 1
    (target_bitdepth, ) = target_bitdepths
    typecode = 'BH'[target_bitdepth > 8]

    # Number of channels
    n_chans = len(rescale)

    for row in rows:
        rescaled_row = array(typecode, iter(row))
        for i in range(n_chans):
            channel = array(
                typecode,
                (int(round(fs[i] * x)) for x in row[i::n_chans]))
            rescaled_row[i::n_chans] = channel
        yield rescaled_row


def pack_rows(rows, bitdepth):
    """Yield packed rows that are a byte array.
    Each byte is packed with the values from several pixels.
    """

    assert bitdepth < 8
    assert 8 % bitdepth == 0

    # samples per byte
    spb = int(8 / bitdepth)

    def make_byte(block):
        """Take a block of (2, 4, or 8) values,
        and pack them into a single byte.
        """

        res = 0
        for v in block:
            res = (res << bitdepth) + v
        return res

    for row in rows:
        a = bytearray(row)
        # Adding padding bytes so we can group into a whole
        # number of spb-tuples.
        n = float(len(a))
        extra = math.ceil(n / spb) * spb - n
        a.extend([0] * int(extra))
        # Pack into bytes.
        # Each block is the samples for one byte.
        blocks = group(a, spb)
        yield bytearray(make_byte(block) for block in blocks)


def unpack_rows(rows):
    """Unpack each row from being 16-bits per value,
    to being a sequence of bytes.
    """
    for row in rows:
        fmt = '!%dH' % len(row)
        yield bytearray(struct.pack(fmt, *row))


def make_palette_chunks(palette):
    """
    Create the byte sequences for a ``PLTE`` and
    if necessary a ``tRNS`` chunk.
    Returned as a pair (*p*, *t*).
    *t* will be ``None`` if no ``tRNS`` chunk is necessary.
    """

    p = bytearray()
    t = bytearray()

    for x in palette:
        p.extend(x[0:3])
        if len(x) > 3:
            t.append(x[3])
    if t:
        return p, t
    return p, None


def check_bitdepth_rescale(
        palette, bitdepth, transparent, alpha, greyscale):
    """
    Returns (bitdepth, rescale) pair.
    """

    if palette:
        if len(bitdepth) != 1:
            raise ValueError(
                "with palette, only a single bitdepth may be used")
        (bitdepth, ) = bitdepth
        if bitdepth not in (1, 2, 4, 8):
            raise ValueError(
                "with palette, bitdepth must be 1, 2, 4, or 8")
        if transparent is not None:
            raise ValueError("transparent and palette not compatible")
        if alpha:
            raise ValueError("alpha and palette not compatible")
        if greyscale:
            raise ValueError("greyscale and palette not compatible")
        return bitdepth, None

    # No palette, check for sBIT chunk generation.

    if greyscale and not alpha:
        # Single channel, L.
        (bitdepth,) = bitdepth
        if bitdepth in (1, 2, 4, 8, 16):
            return bitdepth, None
        if bitdepth > 8:
            targetbitdepth = 16
        elif bitdepth == 3:
            targetbitdepth = 4
        else:
            assert bitdepth in (5, 6, 7)
            targetbitdepth = 8
        return targetbitdepth, [(bitdepth, targetbitdepth)]

    assert alpha or not greyscale

    depth_set = tuple(set(bitdepth))
    if depth_set in [(8,), (16,)]:
        # No sBIT required.
        (bitdepth, ) = depth_set
        return bitdepth, None

    targetbitdepth = (8, 16)[max(bitdepth) > 8]
    return targetbitdepth, [(b, targetbitdepth) for b in bitdepth]


def filter_scanline(type, line, fo, prev=None):
    """Apply a scanline filter to a scanline.
    `type` is the filter type (0 to 4);
    `line` is the current (unfiltered) scanline as a sequence of bytes;
    `prev` is the previous (unfiltered) scanline as a sequence of bytes.
    `fo` is the filter offset;
    normally this is size of a pixel in bytes
    (the number of bytes per sample times the number of channels),
    but when this is < 1 (for bit depths < 8) then the filter offset is 1.
    """

    assert 0 <= type < 5

    # The output array.  Which, pathetically, we extend one-byte at a
    # time (fortunately this is linear).
    out = array('B', [type])

    def sub():
        ai = -fo
        for x in line:
            if ai >= 0:
                x = (x - line[ai]) & 0xff
            out.append(x)
            ai += 1

    def up():
        for i, x in enumerate(line):
            x = (x - prev[i]) & 0xff
            out.append(x)

    def average():
        ai = -fo
        for i, x in enumerate(line):
            if ai >= 0:
                x = (x - ((line[ai] + prev[i]) >> 1)) & 0xff
            else:
                x = (x - (prev[i] >> 1)) & 0xff
            out.append(x)
            ai += 1

    def paeth():
        # http://www.w3.org/TR/PNG/#9Filter-type-4-Paeth
        ai = -fo    # also used for ci
        for i, x in enumerate(line):
            a = 0
            b = prev[i]
            c = 0

            if ai >= 0:
                a = line[ai]
                c = prev[ai]
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                Pr = a
            elif pb <= pc:
                Pr = b
            else:
                Pr = c

            x = (x - Pr) & 0xff
            out.append(x)
            ai += 1

    if not prev:
        # We're on the first line.  Some of the filters can be reduced
        # to simpler cases which makes handling the line "off the top"
        # of the image simpler.  "up" becomes "none"; "paeth" becomes
        # "left" (non-trivial, but true). "average" needs to be handled
        # specially.
        if type == 2:       # "up"
            type = 0
        elif type == 3:
            prev = [0] * len(line)
        elif type == 4:     # "paeth"
            type = 1
    if type == 0:
        out.extend(line)
    elif type == 1:
        sub()
    elif type == 2:
        up()
    elif type == 3:
        average()
    else:   # type == 4
        paeth()
    return out


# Regex for decoding mode string
RegexModeDecode = re.compile("(LA?|RGBA?);?([0-9]*)", flags=re.IGNORECASE)


def from_array(a, mode=None, info={}):
    """Create a PNG :class:`Image` object from a 2- or 3-dimensional
    array.  One application of this function is easy PIL-style saving:
    ``png.from_array(pixels, 'L').save('foo.png')``.

    Unless they are specified using the *info* parameter, the PNG's
    height and width are taken from the array size.  For a 3 dimensional
    array the first axis is the height; the second axis is the width;
    and the third axis is the channel number.  Thus an RGB image that is
    16 pixels high and 8 wide will use an array that is 16x8x3.  For 2
    dimensional arrays the first axis is the height, but the second axis
    is ``width*channels``, so an RGB image that is 16 pixels high and 8
    wide will use a 2-dimensional array that is 16x24 (each row will be
    8*3 = 24 sample values).

    *mode* is a string that specifies the image colour format in a
    PIL-style mode.  It can be:

    ``'L'``
      greyscale (1 channel)
    ``'LA'``
      greyscale with alpha (2 channel)
    ``'RGB'``
      colour image (3 channel)
    ``'RGBA'``
      colour image with alpha (4 channel)

    The mode string can also specify the bit depth (overriding how this
    function normally derives the bit depth, see below).  Appending
    ``';16'`` to the mode will cause the PNG to be 16 bits per channel;
    any decimal from 1 to 16 can be used to specify the bit depth.

    When a 2-dimensional array is used *mode* determines how many
    channels the image has, and so allows the width to be derived from
    the second array dimension.

    The array is expected to be a ``numpy`` array, but it can be any
    suitable Python sequence.  For example, a list of lists can be used:
    ``png.from_array([[0, 255, 0], [255, 0, 255]], 'L')``.  The exact
    rules are: ``len(a)`` gives the first dimension, height;
    ``len(a[0])`` gives the second dimension; ``len(a[0][0])`` gives the
    third dimension, unless an exception is raised in which case a
    2-dimensional array is assumed.  It's slightly more complicated than
    that because an iterator of rows can be used, and it all still
    works.  Using an iterator allows data to be streamed efficiently.

    The bit depth of the PNG is normally taken from the array element's
    datatype (but if *mode* specifies a bitdepth then that is used
    instead).  The array element's datatype is determined in a way which
    is supposed to work both for ``numpy`` arrays and for Python
    ``array.array`` objects.  A 1 byte datatype will give a bit depth of
    8, a 2 byte datatype will give a bit depth of 16.  If the datatype
    does not have an implicit size, for example it is a plain Python
    list of lists, as above, then a default of 8 is used.

    The *info* parameter is a dictionary that can be used to specify
    metadata (in the same style as the arguments to the
    :class:`png.Writer` class).  For this function the keys that are
    useful are:

    height
      overrides the height derived from the array dimensions and allows
      *a* to be an iterable.
    width
      overrides the width derived from the array dimensions.
    bitdepth
      overrides the bit depth derived from the element datatype (but
      must match *mode* if that also specifies a bit depth).

    Generally anything specified in the
    *info* dictionary will override any implicit choices that this
    function would otherwise make, but must match any explicit ones.
    For example, if the *info* dictionary has a ``greyscale`` key then
    this must be true when mode is ``'L'`` or ``'LA'`` and false when
    mode is ``'RGB'`` or ``'RGBA'``.
    """

    # We abuse the *info* parameter by modifying it.  Take a copy here.
    # (Also typechecks *info* to some extent).
    info = dict(info)

    # Syntax check mode string.
    match = RegexModeDecode.match(mode)
    if not match:
        raise Error("mode string should be 'RGB' or 'L;16' or similar.")

    mode, bitdepth = match.groups()
    alpha = 'A' in mode
    if bitdepth:
        bitdepth = int(bitdepth)

    # Colour format.
    if 'greyscale' in info:
        if bool(info['greyscale']) != ('L' in mode):
            raise Error("info['greyscale'] should match mode.")
    info['greyscale'] = 'L' in mode

    if 'alpha' in info:
        if bool(info['alpha']) != alpha:
            raise Error("info['alpha'] should match mode.")
    info['alpha'] = alpha

    # Get bitdepth from *mode* if possible.
    if bitdepth:
        if info.get("bitdepth") and bitdepth != info['bitdepth']:
            raise Error(
                "bitdepth (%d) should match bitdepth of info (%d)." %
                (bitdepth, info['bitdepth']))
        info['bitdepth'] = bitdepth

    # Fill in and/or check entries in *info*.
    # Dimensions.
    if 'size' in info:
        assert len(info["size"]) == 2

        # Check width, height, size all match where used.
        for dimension, axis in [('width', 0), ('height', 1)]:
            if dimension in info:
                if info[dimension] != info['size'][axis]:
                    raise Error(
                        "info[%r] should match info['size'][%r]." %
                        (dimension, axis))
        info['width'], info['height'] = info['size']

    if 'height' not in info:
        try:
            info['height'] = len(a)
        except TypeError:
            raise Error("len(a) does not work, supply info['height'] instead.")

    planes = len(mode)
    if 'planes' in info:
        if info['planes'] != planes:
            raise Error("info['planes'] should match mode.")

    # In order to work out whether we the array is 2D or 3D we need its
    # first row, which requires that we take a copy of its iterator.
    # We may also need the first row to derive width and bitdepth.
    a, t = itertools.tee(a)
    row = next(t)
    del t
    try:
        row[0][0]
        threed = True
        testelement = row[0]
    except (IndexError, TypeError):
        threed = False
        testelement = row
    if 'width' not in info:
        if threed:
            width = len(row)
        else:
            width = len(row) // planes
        info['width'] = width

    if threed:
        # Flatten the threed rows
        a = (itertools.chain.from_iterable(x) for x in a)

    if 'bitdepth' not in info:
        try:
            dtype = testelement.dtype
            # goto the "else:" clause.  Sorry.
        except AttributeError:
            try:
                # Try a Python array.array.
                bitdepth = 8 * testelement.itemsize
            except AttributeError:
                # We can't determine it from the array element's
                # datatype, use a default of 8.
                bitdepth = 8
        else:
            # If we got here without exception, we now assume that
            # the array is a numpy array.
            if dtype.kind == 'b':
                bitdepth = 1
            else:
                bitdepth = 8 * dtype.itemsize
        info['bitdepth'] = bitdepth

    for thing in ["width", "height", "bitdepth", "greyscale", "alpha"]:
        assert thing in info

    return Image(a, info)


# So that refugee's from PIL feel more at home.  Not documented.
fromarray = from_array


class Image:
    """A PNG image.  You can create an :class:`Image` object from
    an array of pixels by calling :meth:`png.from_array`.  It can be
    saved to disk with the :meth:`save` method.
    """

    def __init__(self, rows, info):
        """
        .. note ::

          The constructor is not public.  Please do not call it.
        """

        self.rows = rows
        self.info = info

    def save(self, file):
        """Save the image to *file*.  If *file* looks like an open file
        descriptor then it is used, otherwise it is treated as a
        filename and a fresh file is opened.

        In general, you can only call this method once; after it has
        been called the first time and the PNG image has been saved, the
        source data will have been streamed, and cannot be streamed
        again.
        """

        w = Writer(**self.info)

        try:
            file.write

            def close():
                pass
        except AttributeError:
            file = open(file, 'wb')

            def close():
                file.close()

        try:
            w.write(file, self.rows)
        finally:
            close()


try:
    str(b'dummy', 'ascii')
except TypeError:
    # Typically we get here in Python 2.
    as_str = str
else:
    def as_str(x):
        """
        Convert ASCII bytes to string.
        Only expected to be used in Python 3.
        """
        return str(x, 'ascii')


class Reader:
    """
    PNG decoder in pure Python.
    """

    def __init__(self, _guess=None, **kw):
        """
        Create a PNG decoder object.

        The constructor expects exactly one keyword argument.
        If you supply a positional argument instead,
        it will guess the input type.
        Choose from the following keyword arguments:

        filename
          Name of input file (a PNG file).
        file
          A file-like object (object with a read() method).
        bytes
          ``bytes`` or ``bytearray`` with PNG data.

        """
        if ((_guess is not None and len(kw) != 0) or
                (_guess is None and len(kw) != 1)):
            raise TypeError("Reader() takes exactly 1 argument")

        # Will be the first 8 bytes, later on.  See validate_signature.
        self.signature = None
        self.transparent = None
        # A pair of (len,type) if a chunk has been read but its data and
        # checksum have not (in other words the file position is just
        # past the 4 bytes that specify the chunk type).
        # See preamble method for how this is used.
        self.atchunk = None

        if _guess is not None:
            if isarray(_guess):
                kw["bytes"] = _guess
            elif isinstance(_guess, str):
                kw["filename"] = _guess
            elif hasattr(_guess, 'read'):
                kw["file"] = _guess

        if "filename" in kw:
            self.file = open(kw["filename"], "rb")
        elif "file" in kw:
            self.file = kw["file"]
        elif "bytes" in kw:
            self.file = io.BytesIO(kw["bytes"])
        else:
            raise TypeError("expecting filename, file or bytes array")

    def chunk(self, lenient=False):
        """
        Read the next PNG chunk from the input file;
        returns a (*type*, *data*) tuple.
        *type* is the chunk's type as a byte string
        (all PNG chunk types are 4 bytes long).
        *data* is the chunk's data content, as a byte string.

        If the optional `lenient` argument evaluates to `True`,
        checksum failures will raise warnings rather than exceptions.
        """

        self.validate_signature()

        # http://www.w3.org/TR/PNG/#5Chunk-layout
        if not self.atchunk:
            self.atchunk = self.chunklentype()
        length, type = self.atchunk
        self.atchunk = None
        data = self.file.read(length)
        if len(data) != length:
            raise ChunkError(
                'Chunk %s too short for required %i octets.'
                % (type, length))
        checksum = self.file.read(4)
        if len(checksum) != 4:
            raise ChunkError('Chunk %s too short for checksum.' % type)
        verify = zlib.crc32(type)
        verify = zlib.crc32(data, verify)
        # Whether the output from zlib.crc32 is signed or not varies
        # according to hideous implementation details, see
        # http://bugs.python.org/issue1202 .
        # We coerce it to be positive here (in a way which works on
        # Python 2.3 and older).
        verify &= 2**32 - 1
        verify = struct.pack('!I', verify)
        if checksum != verify:
            (a, ) = struct.unpack('!I', checksum)
            (b, ) = struct.unpack('!I', verify)
            message = ("Checksum error in %s chunk: 0x%08X != 0x%08X."
                       % (type, a, b))
            if lenient:
                warnings.warn(message, RuntimeWarning)
            else:
                raise ChunkError(message)
        return type, data

    def chunks(self):
        """Return an iterator that will yield each chunk as a
        (*chunktype*, *content*) pair.
        """

        while True:
            t, v = self.chunk()
            yield t, v
            if t == b'IEND':
                break

    def undo_filter(self, filter_type, scanline, previous):
        """Undo the filter for a scanline.  `scanline` is a sequence of
        bytes that does not include the initial filter type byte.
        `previous` is decoded previous scanline (for straightlaced
        images this is the previous pixel row, but for interlaced
        images, it is the previous scanline in the reduced image, which
        in general is not the previous pixel row in the final image).
        When there is no previous scanline (the first row of a
        straightlaced image, or the first row in one of the passes in an
        interlaced image), then this argument should be ``None``.

        The scanline will have the effects of filtering removed, and the
        result will be returned as a fresh sequence of bytes.
        """

        # :todo: Would it be better to update scanline in place?
        # Yes, with the Cython extension making the undo_filter fast,
        # updating scanline inplace makes the code 3 times faster
        # (reading 50 images of 800x800 went from 40s to 16s)
        result = scanline

        if filter_type == 0:
            return result

        if filter_type not in (1, 2, 3, 4):
            raise FormatError(
                'Invalid PNG Filter Type.  '
                'See http://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters .')

        # Filter unit.  The stride from one pixel to the corresponding
        # byte from the previous pixel.  Normally this is the pixel
        # size in bytes, but when this is smaller than 1, the previous
        # byte is used instead.
        fu = max(1, self.psize)

        # For the first line of a pass, synthesize a dummy previous
        # line.  An alternative approach would be to observe that on the
        # first line 'up' is the same as 'null', 'paeth' is the same
        # as 'sub', with only 'average' requiring any special case.
        if not previous:
            previous = bytearray([0] * len(scanline))

        # Call appropriate filter algorithm.  Note that 0 has already
        # been dealt with.
        fn = (None,
              pngfilters.undo_filter_sub,
              pngfilters.undo_filter_up,
              pngfilters.undo_filter_average,
              pngfilters.undo_filter_paeth)[filter_type]
        fn(fu, scanline, previous, result)
        return result

    def deinterlace(self, raw):
        """
        Read raw pixel data, undo filters, deinterlace, and flatten.
        Return in flat row flat pixel format.
        """

        # Values per row (of the target image)
        vpr = self.width * self.planes

        # Values per image
        vpi = vpr * self.height
        # Interleaving writes to the output array randomly
        # (well, not quite), so the entire output array must be in memory.
        # Make a result array, and make it big enough.
        if self.bitdepth > 8:
            a = array('H', [0] * vpi)
        else:
            a = bytearray([0] * vpi)
        source_offset = 0

        for lines in adam7_generate(self.width, self.height):
            # The previous (reconstructed) scanline.
            # `None` at the beginning of a pass
            # to indicate that there is no previous line.
            recon = None
            for x, y, xstep in lines:
                # Pixels per row (reduced pass image)
                ppr = int(math.ceil((self.width - x) / float(xstep)))
                # Row size in bytes for this pass.
                row_size = int(math.ceil(self.psize * ppr))

                filter_type = raw[source_offset]
                source_offset += 1
                scanline = raw[source_offset: source_offset + row_size]
                source_offset += row_size
                recon = self.undo_filter(filter_type, scanline, recon)
                # Convert so that there is one element per pixel value
                flat = self.bytes_to_values(recon, width=ppr)
                if xstep == 1:
                    assert x == 0
                    offset = y * vpr
                    a[offset: offset + vpr] = flat
                else:
                    offset = y * vpr + x * self.planes
                    end_offset = (y + 1) * vpr
                    skip = self.planes * xstep
                    for i in range(self.planes):
                        a[offset + i: end_offset: skip] = \
                            flat[i:: self.planes]

        return a

    def iter_bytes_to_values(self, byte_rows):
        """Iterator that yields each scanline in boxed row flat pixel format.
        `byte_rows` should be an iterator that yields
        the bytes of each row in turn.
        """

        for row in byte_rows:
            yield self.bytes_to_values(row)

    def bytes_to_values(self, bs, width=None):
        """Convert a row of bytes into a flat row of values.
        Result will be a freshly allocated object, not shared with
        argument.
        """

        if self.bitdepth == 8:
            return bytearray(bs)
        if self.bitdepth == 16:
            # Conversion to bytes only required for Python 2.6
            bs = bytes(bs)
            return array('H',
                         struct.unpack('!%dH' % (len(bs) // 2), bs))

        assert self.bitdepth < 8
        if width is None:
            width = self.width
        # Samples per byte
        spb = 8 // self.bitdepth
        out = bytearray()
        mask = 2**self.bitdepth - 1
        shifts = [self.bitdepth * i
                  for i in reversed(list(range(spb)))]
        for o in bs:
            out.extend([mask & (o >> i) for i in shifts])
        return out[:width]

    def iter_straight_byte_rows(self, byte_blocks):
        """Iterator that undoes the effect of filtering;
        yields each row as a sequence of bytes (in serialised format).
        Assumes input is straightlaced.
        `byte_blocks` should be an iterable that yields the raw bytes
        in blocks of arbitrary size.
        """

        # length of row, in bytes
        rb = self.row_bytes
        a = bytearray()
        # The previous (reconstructed) scanline.
        # None indicates first line of image.
        recon = None
        for some_bytes in byte_blocks:
            a.extend(some_bytes)
            while len(a) >= rb + 1:
                filter_type = a[0]
                scanline = a[1: rb + 1]
                del a[: rb + 1]
                recon = self.undo_filter(filter_type, scanline, recon)
                yield recon
        if len(a) != 0:
            # :file:format We get here with a file format error:
            # when the available bytes (after decompressing) do not
            # pack into exact rows.
            raise FormatError('Wrong size for decompressed IDAT chunk.')
        assert len(a) == 0

    def validate_signature(self):
        """If signature (header) has not been read then read and
        validate it; otherwise do nothing.
        """

        if self.signature:
            return
        self.signature = self.file.read(8)
        if self.signature != signature:
            raise FormatError("PNG file has invalid signature.")

    def preamble(self, lenient=False):
        """
        Extract the image metadata by reading the initial part of
        the PNG file up to the start of the ``IDAT`` chunk.  All the
        chunks that precede the ``IDAT`` chunk are read and either
        processed for metadata or discarded.

        If the optional `lenient` argument evaluates to `True`, checksum
        failures will raise warnings rather than exceptions.
        """

        self.validate_signature()

        while True:
            if not self.atchunk:
                self.atchunk = self.chunklentype()
                if self.atchunk is None:
                    raise FormatError('This PNG file has no IDAT chunks.')
            if self.atchunk[1] == b'IDAT':
                return
            self.process_chunk(lenient=lenient)

    def chunklentype(self):
        """Reads just enough of the input to determine the next
        chunk's length and type, returned as a (*length*, *type*) pair
        where *type* is a string.  If there are no more chunks, ``None``
        is returned.
        """

        x = self.file.read(8)
        if not x:
            return None
        if len(x) != 8:
            raise FormatError(
                'End of file whilst reading chunk length and type.')
        length, type = struct.unpack('!I4s', x)
        if length > 2 ** 31 - 1:
            raise FormatError('Chunk %s is too large: %d.' % (type, length))
        return length, type

    def process_chunk(self, lenient=False):
        """Process the next chunk and its data.  This only processes the
        following chunk types, all others are ignored: ``IHDR``,
        ``PLTE``, ``bKGD``, ``tRNS``, ``gAMA``, ``sBIT``, ``pHYs``.

        If the optional `lenient` argument evaluates to `True`,
        checksum failures will raise warnings rather than exceptions.
        """

        type, data = self.chunk(lenient=lenient)
        method = '_process_' + as_str(type)
        m = getattr(self, method, None)
        if m:
            m(data)

    def _process_IHDR(self, data):
        # http://www.w3.org/TR/PNG/#11IHDR
        if len(data) != 13:
            raise FormatError('IHDR chunk has incorrect length.')
        (self.width, self.height, self.bitdepth, self.color_type,
         self.compression, self.filter,
         self.interlace) = struct.unpack("!2I5B", data)

        check_bitdepth_colortype(self.bitdepth, self.color_type)

        if self.compression != 0:
            raise Error("unknown compression method %d" % self.compression)
        if self.filter != 0:
            raise FormatError(
                "Unknown filter method %d,"
                " see http://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters ."
                % self.filter)
        if self.interlace not in (0, 1):
            raise FormatError(
                "Unknown interlace method %d, see "
                "http://www.w3.org/TR/2003/REC-PNG-20031110/#8InterlaceMethods"
                " ."
                % self.interlace)

        # Derived values
        # http://www.w3.org/TR/PNG/#6Colour-values
        colormap = bool(self.color_type & 1)
        greyscale = not(self.color_type & 2)
        alpha = bool(self.color_type & 4)
        color_planes = (3, 1)[greyscale or colormap]
        planes = color_planes + alpha

        self.colormap = colormap
        self.greyscale = greyscale
        self.alpha = alpha
        self.color_planes = color_planes
        self.planes = planes
        self.psize = float(self.bitdepth) / float(8) * planes
        if int(self.psize) == self.psize:
            self.psize = int(self.psize)
        self.row_bytes = int(math.ceil(self.width * self.psize))
        # Stores PLTE chunk if present, and is used to check
        # chunk ordering constraints.
        self.plte = None
        # Stores tRNS chunk if present, and is used to check chunk
        # ordering constraints.
        self.trns = None
        # Stores sBIT chunk if present.
        self.sbit = None

    def _process_PLTE(self, data):
        # http://www.w3.org/TR/PNG/#11PLTE
        if self.plte:
            warnings.warn("Multiple PLTE chunks present.")
        self.plte = data
        if len(data) % 3 != 0:
            raise FormatError(
                "PLTE chunk's length should be a multiple of 3.")
        if len(data) > (2 ** self.bitdepth) * 3:
            raise FormatError("PLTE chunk is too long.")
        if len(data) == 0:
            raise FormatError("Empty PLTE is not allowed.")

    def _process_bKGD(self, data):
        try:
            if self.colormap:
                if not self.plte:
                    warnings.warn(
                        "PLTE chunk is required before bKGD chunk.")
                self.background = struct.unpack('B', data)
            else:
                self.background = struct.unpack("!%dH" % self.color_planes,
                                                data)
        except struct.error:
            raise FormatError("bKGD chunk has incorrect length.")

    def _process_tRNS(self, data):
        # http://www.w3.org/TR/PNG/#11tRNS
        self.trns = data
        if self.colormap:
            if not self.plte:
                warnings.warn("PLTE chunk is required before tRNS chunk.")
            else:
                if len(data) > len(self.plte) / 3:
                    # Was warning, but promoted to Error as it
                    # would otherwise cause pain later on.
                    raise FormatError("tRNS chunk is too long.")
        else:
            if self.alpha:
                raise FormatError(
                    "tRNS chunk is not valid with colour type %d." %
                    self.color_type)
            try:
                self.transparent = \
                    struct.unpack("!%dH" % self.color_planes, data)
            except struct.error:
                raise FormatError("tRNS chunk has incorrect length.")

    def _process_gAMA(self, data):
        try:
            self.gamma = struct.unpack("!L", data)[0] / 100000.0
        except struct.error:
            raise FormatError("gAMA chunk has incorrect length.")

    def _process_sBIT(self, data):
        self.sbit = data
        if (self.colormap and len(data) != 3 or
                not self.colormap and len(data) != self.planes):
            raise FormatError("sBIT chunk has incorrect length.")

    def _process_pHYs(self, data):
        # http://www.w3.org/TR/PNG/#11pHYs
        self.phys = data
        fmt = "!LLB"
        if len(data) != struct.calcsize(fmt):
            raise FormatError("pHYs chunk has incorrect length.")
        self.x_pixels_per_unit, self.y_pixels_per_unit, unit = \
            struct.unpack(fmt, data)
        self.unit_is_meter = bool(unit)

    def read(self, lenient=False):
        """
        Read the PNG file and decode it.  Returns (`width`, `height`,
        `pixels`, `metadata`).

        May use excessive memory.

        `pixels` are returned in boxed row flat pixel format.

        If the optional `lenient` argument evaluates to True,
        checksum failures will raise warnings rather than exceptions.
        """

        def iteridat():
            """Iterator that yields all the ``IDAT`` chunks as strings."""
            while True:
                try:
                    type, data = self.chunk(lenient=lenient)
                except ValueError as e:
                    raise ChunkError(e.args[0])
                if type == b'IEND':
                    # http://www.w3.org/TR/PNG/#11IEND
                    break
                if type != b'IDAT':
                    continue
                # type == b'IDAT'
                # http://www.w3.org/TR/PNG/#11IDAT
                if self.colormap and not self.plte:
                    warnings.warn("PLTE chunk is required before IDAT chunk")
                yield data

        self.preamble(lenient=lenient)
        raw = decompress(iteridat())

        if self.interlace:
            raw = bytearray(itertools.chain(*raw))
            arraycode = 'BH'[self.bitdepth > 8]
            # Like :meth:`group` but producing an array.array object for
            # each row.
            rows = map(lambda *row: array(arraycode, row),
                       * [iter(self.deinterlace(raw))] *
                       (self.width * self.planes))
        else:
            rows = self.iter_bytes_to_values(self.iter_straight_byte_rows(raw))
        meta = dict()
        for attr in 'greyscale alpha planes bitdepth interlace'.split():
            meta[attr] = getattr(self, attr)
        meta['size'] = (self.width, self.height)
        for attr in 'gamma transparent background'.split():
            a = getattr(self, attr, None)
            if a is not None:
                meta[attr] = a
        if getattr(self, 'x_pixels_per_unit', None):
            meta['physical'] = Resolution(self.x_pixels_per_unit,
                                          self.y_pixels_per_unit,
                                          self.unit_is_meter)
        if self.plte:
            meta['palette'] = self.palette()
        return self.width, self.height, rows, meta

    def read_flat(self):
        """
        Read a PNG file and decode it into flat row flat pixel format.
        Returns (*width*, *height*, *pixels*, *metadata*).

        May use excessive memory.

        `pixels` are returned in flat row flat pixel format.

        See also the :meth:`read` method which returns pixels in the
        more stream-friendly boxed row flat pixel format.
        """

        x, y, pixel, meta = self.read()
        arraycode = 'BH'[meta['bitdepth'] > 8]
        pixel = array(arraycode, itertools.chain(*pixel))
        return x, y, pixel, meta

    def palette(self, alpha='natural'):
        """Returns a palette that is a sequence of 3-tuples or 4-tuples,
        synthesizing it from the ``PLTE`` and ``tRNS`` chunks.
        These chunks should have already been processed (for example,
        by calling the :meth:`preamble` method).
        All the tuples are the same size:
        3-tuples if there is no ``tRNS`` chunk,
        4-tuples when there is a ``tRNS`` chunk.

        Assumes that the image is colour type
        3 and therefore a ``PLTE`` chunk is required.

        If the `alpha` argument is ``'force'`` then an alpha channel is
        always added, forcing the result to be a sequence of 4-tuples.
        """

        if not self.plte:
            raise FormatError(
                "Required PLTE chunk is missing in colour type 3 image.")
        plte = group(array('B', self.plte), 3)
        if self.trns or alpha == 'force':
            trns = array('B', self.trns or [])
            trns.extend([255] * (len(plte) - len(trns)))
            plte = list(map(operator.add, plte, group(trns, 1)))
        return plte

    def asDirect(self):
        """Returns the image data as a direct representation of an
        ``x * y * planes`` array.  This method is intended to remove the
        need for callers to deal with palettes and transparency
        themselves.  Images with a palette (colour type 3)
        are converted to RGB or RGBA; images with transparency (a
        ``tRNS`` chunk) are converted to LA or RGBA as appropriate.
        When returned in this format the pixel values represent the
        colour value directly without needing to refer to palettes or
        transparency information.

        Like the :meth:`read` method this method returns a 4-tuple:

        (*width*, *height*, *pixels*, *meta*)

        This method normally returns pixel values with the bit depth
        they have in the source image, but when the source PNG has an
        ``sBIT`` chunk it is inspected and can reduce the bit depth of
        the result pixels; pixel values will be reduced according to
        the bit depth specified in the ``sBIT`` chunk (PNG nerds should
        note a single result bit depth is used for all channels; the
        maximum of the ones specified in the ``sBIT`` chunk.  An RGB565
        image will be rescaled to 6-bit RGB666).

        The *meta* dictionary that is returned reflects the `direct`
        format and not the original source image.  For example, an RGB
        source image with a ``tRNS`` chunk to represent a transparent
        colour, will have ``planes=3`` and ``alpha=False`` for the
        source image, but the *meta* dictionary returned by this method
        will have ``planes=4`` and ``alpha=True`` because an alpha
        channel is synthesized and added.

        *pixels* is the pixel data in boxed row flat pixel format (just
        like the :meth:`read` method).

        All the other aspects of the image data are not changed.
        """

        self.preamble()

        # Simple case, no conversion necessary.
        if not self.colormap and not self.trns and not self.sbit:
            return self.read()

        x, y, pixels, meta = self.read()

        if self.colormap:
            meta['colormap'] = False
            meta['alpha'] = bool(self.trns)
            meta['bitdepth'] = 8
            meta['planes'] = 3 + bool(self.trns)
            plte = self.palette()

            def iterpal(pixels):
                for row in pixels:
                    row = [plte[x] for x in row]
                    yield array('B', itertools.chain(*row))
            pixels = iterpal(pixels)
        elif self.trns:
            # It would be nice if there was some reasonable way
            # of doing this without generating a whole load of
            # intermediate tuples.  But tuples does seem like the
            # easiest way, with no other way clearly much simpler or
            # much faster.  (Actually, the L to LA conversion could
            # perhaps go faster (all those 1-tuples!), but I still
            # wonder whether the code proliferation is worth it)
            it = self.transparent
            maxval = 2 ** meta['bitdepth'] - 1
            planes = meta['planes']
            meta['alpha'] = True
            meta['planes'] += 1
            typecode = 'BH'[meta['bitdepth'] > 8]

            def itertrns(pixels):
                for row in pixels:
                    # For each row we group it into pixels, then form a
                    # characterisation vector that says whether each
                    # pixel is opaque or not.  Then we convert
                    # True/False to 0/maxval (by multiplication),
                    # and add it as the extra channel.
                    row = group(row, planes)
                    opa = map(it.__ne__, row)
                    opa = map(maxval.__mul__, opa)
                    opa = list(zip(opa))    # convert to 1-tuples
                    yield array(
                        typecode,
                        itertools.chain(*map(operator.add, row, opa)))
            pixels = itertrns(pixels)
        targetbitdepth = None
        if self.sbit:
            sbit = struct.unpack('%dB' % len(self.sbit), self.sbit)
            targetbitdepth = max(sbit)
            if targetbitdepth > meta['bitdepth']:
                raise Error('sBIT chunk %r exceeds bitdepth %d' %
                            (sbit, self.bitdepth))
            if min(sbit) <= 0:
                raise Error('sBIT chunk %r has a 0-entry' % sbit)
            if targetbitdepth == meta['bitdepth']:
                targetbitdepth = None
        if targetbitdepth:
            shift = meta['bitdepth'] - targetbitdepth
            meta['bitdepth'] = targetbitdepth

            def itershift(pixels):
                for row in pixels:
                    yield [p >> shift for p in row]
            pixels = itershift(pixels)
        return x, y, pixels, meta

    def asFloat(self, maxval=1.0):
        """Return image pixels as per :meth:`asDirect` method, but scale
        all pixel values to be floating point values between 0.0 and
        *maxval*.
        """

        x, y, pixels, info = self.asDirect()
        sourcemaxval = 2 ** info['bitdepth'] - 1
        del info['bitdepth']
        info['maxval'] = float(maxval)
        factor = float(maxval) / float(sourcemaxval)

        def iterfloat():
            for row in pixels:
                yield [factor * p for p in row]
        return x, y, iterfloat(), info

    def _as_rescale(self, get, targetbitdepth):
        """Helper used by :meth:`asRGB8` and :meth:`asRGBA8`."""

        width, height, pixels, meta = get()
        maxval = 2**meta['bitdepth'] - 1
        targetmaxval = 2**targetbitdepth - 1
        factor = float(targetmaxval) / float(maxval)
        meta['bitdepth'] = targetbitdepth

        def iterscale():
            for row in pixels:
                yield [int(round(x * factor)) for x in row]
        if maxval == targetmaxval:
            return width, height, pixels, meta
        else:
            return width, height, iterscale(), meta

    def asRGB8(self):
        """Return the image data as an RGB pixels with 8-bits per
        sample.  This is like the :meth:`asRGB` method except that
        this method additionally rescales the values so that they
        are all between 0 and 255 (8-bit).  In the case where the
        source image has a bit depth < 8 the transformation preserves
        all the information; where the source image has bit depth
        > 8, then rescaling to 8-bit values loses precision.  No
        dithering is performed.  Like :meth:`asRGB`, an alpha channel
        in the source image will raise an exception.

        This function returns a 4-tuple:
        (*width*, *height*, *pixels*, *metadata*).
        *width*, *height*, *metadata* are as per the
        :meth:`read` method.

        *pixels* is the pixel data in boxed row flat pixel format.
        """

        return self._as_rescale(self.asRGB, 8)

    def asRGBA8(self):
        """Return the image data as RGBA pixels with 8-bits per
        sample.  This method is similar to :meth:`asRGB8` and
        :meth:`asRGBA`:  The result pixels have an alpha channel, *and*
        values are rescaled to the range 0 to 255.  The alpha channel is
        synthesized if necessary (with a small speed penalty).
        """

        return self._as_rescale(self.asRGBA, 8)

    def asRGB(self):
        """Return image as RGB pixels.  RGB colour images are passed
        through unchanged; greyscales are expanded into RGB
        triplets (there is a small speed overhead for doing this).

        An alpha channel in the source image will raise an
        exception.

        The return values are as for the :meth:`read` method
        except that the *metadata* reflect the returned pixels, not the
        source image.  In particular, for this method
        ``metadata['greyscale']`` will be ``False``.
        """

        width, height, pixels, meta = self.asDirect()
        if meta['alpha']:
            raise Error("will not convert image with alpha channel to RGB")
        if not meta['greyscale']:
            return width, height, pixels, meta
        meta['greyscale'] = False

        if meta['bitdepth'] > 8:
            def newarray():
                return array('H', [0])
        else:
            def newarray():
                return bytearray([0])

        def iterrgb():
            for row in pixels:
                a = newarray() * 3 * width
                for i in range(3):
                    a[i::3] = row
                yield a
        return width, height, iterrgb(), meta

    def asRGBA(self):
        """Return image as RGBA pixels.  Greyscales are expanded into
        RGB triplets; an alpha channel is synthesized if necessary.
        The return values are as for the :meth:`read` method
        except that the *metadata* reflect the returned pixels, not the
        source image.  In particular, for this method
        ``metadata['greyscale']`` will be ``False``, and
        ``metadata['alpha']`` will be ``True``.
        """

        width, height, pixels, meta = self.asDirect()
        if meta['alpha'] and not meta['greyscale']:
            return width, height, pixels, meta
        typecode = 'BH'[meta['bitdepth'] > 8]
        maxval = 2**meta['bitdepth'] - 1
        maxbuffer = struct.pack('=' + typecode, maxval) * 4 * width

        if meta['bitdepth'] > 8:
            def newarray():
                return array('H', maxbuffer)
        else:
            def newarray():
                return bytearray(maxbuffer)

        if meta['alpha'] and meta['greyscale']:
            # LA to RGBA
            def convert():
                for row in pixels:
                    # Create a fresh target row, then copy L channel
                    # into first three target channels, and A channel
                    # into fourth channel.
                    a = newarray()
                    pngfilters.convert_la_to_rgba(row, a)
                    yield a
        elif meta['greyscale']:
            # L to RGBA
            def convert():
                for row in pixels:
                    a = newarray()
                    pngfilters.convert_l_to_rgba(row, a)
                    yield a
        else:
            assert not meta['alpha'] and not meta['greyscale']
            # RGB to RGBA

            def convert():
                for row in pixels:
                    a = newarray()
                    pngfilters.convert_rgb_to_rgba(row, a)
                    yield a
        meta['alpha'] = True
        meta['greyscale'] = False
        return width, height, convert(), meta


def decompress(data_blocks):
    """`data_blocks` should be an iterable that yields the
    compressed data (from the ``IDAT`` chunks).
    This yields decompressed byte strings.
    """

    # Currently, with no max_length parameter to decompress,
    # this routine will do one yield per IDAT chunk: Not very
    # incremental.
    d = zlib.decompressobj()
    # Each IDAT chunk is passed to the decompressor, then any
    # remaining state is decompressed out.
    for data in data_blocks:
        # :todo: add a max_length argument here to limit output size.
        yield bytearray(d.decompress(data))
    yield bytearray(d.flush())


def check_bitdepth_colortype(bitdepth, colortype):
    """Check that `bitdepth` and `colortype` are both valid,
    and specified in a valid combination. Returns if valid,
    raise an Exception if not valid.
    """

    if bitdepth not in (1, 2, 4, 8, 16):
        raise FormatError("invalid bit depth %d" % bitdepth)
    if colortype not in (0, 2, 3, 4, 6):
        raise FormatError("invalid colour type %d" % colortype)
    # Check indexed (palettized) images have 8 or fewer bits
    # per pixel; check only indexed or greyscale images have
    # fewer than 8 bits per pixel.
    if colortype & 1 and bitdepth > 8:
        raise FormatError(
            "Indexed images (colour type %d) cannot"
            " have bitdepth > 8 (bit depth %d)."
            " See http://www.w3.org/TR/2003/REC-PNG-20031110/#table111 ."
            % (bitdepth, colortype))
    if bitdepth < 8 and colortype not in (0, 3):
        raise FormatError(
            "Illegal combination of bit depth (%d)"
            " and colour type (%d)."
            " See http://www.w3.org/TR/2003/REC-PNG-20031110/#table111 ."
            % (bitdepth, colortype))


def is_natural(x):
    """A non-negative integer."""
    try:
        is_integer = int(x) == x
    except (TypeError, ValueError):
        return False
    return is_integer and x >= 0


# === Support for users without Cython ===

try:
    pngfilters
except NameError:
    class pngfilters(object):
        def undo_filter_sub(filter_unit, scanline, previous, result):
            """Undo sub filter."""

            ai = 0
            # Loops starts at index fu.  Observe that the initial part
            # of the result is already filled in correctly with
            # scanline.
            for i in range(filter_unit, len(result)):
                x = scanline[i]
                a = result[ai]
                result[i] = (x + a) & 0xff
                ai += 1
        undo_filter_sub = staticmethod(undo_filter_sub)

        def undo_filter_up(filter_unit, scanline, previous, result):
            """Undo up filter."""

            for i in range(len(result)):
                x = scanline[i]
                b = previous[i]
                result[i] = (x + b) & 0xff
        undo_filter_up = staticmethod(undo_filter_up)

        def undo_filter_average(filter_unit, scanline, previous, result):
            """Undo up filter."""

            ai = -filter_unit
            for i in range(len(result)):
                x = scanline[i]
                if ai < 0:
                    a = 0
                else:
                    a = result[ai]
                b = previous[i]
                result[i] = (x + ((a + b) >> 1)) & 0xff
                ai += 1
        undo_filter_average = staticmethod(undo_filter_average)

        def undo_filter_paeth(filter_unit, scanline, previous, result):
            """Undo Paeth filter."""

            # Also used for ci.
            ai = -filter_unit
            for i in range(len(result)):
                x = scanline[i]
                if ai < 0:
                    a = c = 0
                else:
                    a = result[ai]
                    c = previous[ai]
                b = previous[i]
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                if pa <= pb and pa <= pc:
                    pr = a
                elif pb <= pc:
                    pr = b
                else:
                    pr = c
                result[i] = (x + pr) & 0xff
                ai += 1
        undo_filter_paeth = staticmethod(undo_filter_paeth)

        def convert_la_to_rgba(row, result):
            for i in range(3):
                result[i::4] = row[0::2]
            result[3::4] = row[1::2]
        convert_la_to_rgba = staticmethod(convert_la_to_rgba)

        def convert_l_to_rgba(row, result):
            """Convert a grayscale image to RGBA. This method assumes
            the alpha channel in result is already correctly
            initialized.
            """
            for i in range(3):
                result[i::4] = row
        convert_l_to_rgba = staticmethod(convert_l_to_rgba)

        def convert_rgb_to_rgba(row, result):
            """Convert an RGB image to RGBA. This method assumes the
            alpha channel in result is already correctly initialized.
            """
            for i in range(3):
                result[i::4] = row[i::3]
        convert_rgb_to_rgba = staticmethod(convert_rgb_to_rgba)


def main(argv):
    """
    Run the PNG encoder with options from the command line.
    """

    # Parse command line arguments
    from optparse import OptionParser
    version = '%prog ' + __version__
    parser = OptionParser(version=version)
    parser.set_usage("%prog [options] [imagefile]")

    (options, args) = parser.parse_args(args=argv[1:])

    # Prepare input and output files
    if len(args) == 0:
        infilename = '-'
        infile = sys.stdin
    elif len(args) == 1:
        infilename = args[0]
        infile = open(infilename, 'rb')
    else:
        parser.error("more than one input file")

    image = Reader(file=infile)
    image


if __name__ == '__main__':
    try:
        main(sys.argv)
    except Error as e:
        print(e, file=sys.stderr)
