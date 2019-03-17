# This file comprises the tests that are internally validated (as
# opposed to tests which produce output files that are externally
# validated).  Primarily they are unittests.

# There is a read/write asymmetry: It is fairly easy to
# internally validate the results of reading a PNG file because we
# can know what pixels it should produce, but when writing a PNG
# file many choices are possible. The only thing we can do is read
# it back in again, which merely checks consistency, not that the
# PNG file we produce is valid.

# Run the tests from the command line:
#   python -m test_png
# If you have nose installed you can use that:
#   nosetests .

from __future__ import print_function

import glob
import itertools
import os
import struct
import sys
# http://www.python.org/doc/2.4.4/lib/module-unittest.html
import unittest
import zlib

from array import array
from io import BytesIO

try:
    import numpy
except ImportError:
    numpy = False

import png
import pngsuite

_palette3 = [
    (255, 255, 255),
    (200, 120, 120),
    (50, 99, 50),
]


def topngbytes(name, rows, x, y, **k):
    """
    Convenience function for creating a PNG file "in memory" as
    a string.  Creates a :class:`Writer` instance using the keyword
    arguments, then passes `rows` to its :meth:`Writer.write` method.
    The resulting PNG file is returned as bytes.  `name` is used
    to identify the file for debugging.
    """

    import os

    if os.environ.get('PYPNG_TEST_FILENAME'):
        print(name, file=sys.stderr)
    f = BytesIO()
    w = png.Writer(x, y, **k)
    w.write(f, rows)
    if os.environ.get('PYPNG_TEST_TMP'):
        w = open(name, 'wb')
        w.write(f.getvalue())
        w.close()
    return f.getvalue()


def mycallersname():
    """Returns the name of the caller of the caller of this function
    (hence the name of the caller of the function in which
    "mycallersname()" textually appears).  Returns None if this cannot
    be determined.
    """

    # http://docs.python.org/library/inspect.html#the-interpreter-stack
    import inspect

    frame = inspect.currentframe()
    if not frame:
        return None
    frame_, filename_, lineno_, funname, linelist_, listi_ = (
        inspect.getouterframes(frame)[2])
    return funname


def seq_to_bytes(s):
    """Convert a sequence of integers to a *bytes* instance.  Good for
    plastering over Python 2 / Python 3 cracks.
    """

    fmt = "{0}B".format(len(s))

    return struct.pack(fmt, *s)


class Test(unittest.TestCase):
    # This member is used by the superclass.  If we don't define a new
    # class here then when we use self.assertRaises() and the PyPNG code
    # raises an assertion then we get no proper traceback.  I can't work
    # out why, but defining a new class here means we get a proper
    # traceback.
    class failureException(Exception):
        pass

    def test_L8(self):
        """Test L8."""
        return self.helper_L(8)

    def test_L3(self):
        """Test L3."""
        return self.helper_L(3)

    def test_L4(self):
        """Test L4."""
        return self.helper_L(4)

    def test_L7(self):
        """Test L7."""
        return self.helper_L(7)

    def test_L9(self):
        """Test L9."""
        return self.helper_L(9)

    def test_L12(self):
        """Test L12."""
        return self.helper_L(12)

    def helper_L(self, n):
        mask = (1 << n) - 1
        # Use small chunk_limit so that multiple chunk writing is
        # tested.  Making it a test for Issue 20 (googlecode).
        w = png.Writer(15, 17, greyscale=True, bitdepth=n, chunk_limit=99)
        f = BytesIO()
        source_pixels = bytearray(mask & x for x in range(1, 256))
        w.write_array(f, source_pixels)
        r = png.Reader(bytes=f.getvalue())
        x, y, pixels, meta = r.asDirect()
        self.assertEqual(x, 15)
        self.assertEqual(y, 17)
        self.assertEqual(list(itertools.chain(*pixels)),
                         list(source_pixels))

    def test_L2(self):
        """Test L2 (and asRGB8)."""
        w = png.Writer(1, 4, greyscale=True, bitdepth=2)
        f = BytesIO()
        w.write_array(f, array('B', range(4)))
        r = png.Reader(bytes=f.getvalue())
        x, y, pixels, meta = r.asRGB8()
        self.assertEqual(x, 1)
        self.assertEqual(y, 4)
        for i, row in enumerate(pixels):
            self.assertEqual(len(row), 3)
            self.assertEqual(list(row), [0x55 * i] * 3)

    def test_LA4(self):
        """Create an LA image with bitdepth 4."""
        bytes = topngbytes('la4.png', [[5, 12]], 1, 1,
                           greyscale=True, alpha=True, bitdepth=4)
        sbit = None
        for chunk_type, content in png.Reader(bytes=bytes).chunks():
            if chunk_type == b'sBIT':
                sbit = content
                break
        self.assertEqual(sbit, b'\x04\x04')

    def test_P2(self):
        """2-bit palette."""
        a, b, c = _palette3
        w = png.Writer(1, 4, bitdepth=2, palette=_palette3)
        f = BytesIO()
        w.write_array(f, array('B', (0, 1, 1, 2)))
        r = png.Reader(bytes=f.getvalue())
        x, y, pixels, meta = r.asRGB8()
        self.assertEqual(x, 1)
        self.assertEqual(y, 4)
        self.assertEqual([list(row) for row in pixels],
                         [list(row) for row in [a, b, b, c]])

    def test_palette_trns(self):
        """Test colour type 3 and tRNS chunk (and 4-bit palette)."""
        a = (50, 99, 50, 50)
        b = (200, 120, 120, 80)
        c = (255, 255, 255)
        d = (200, 120, 120)
        e = (50, 99, 50)
        w = png.Writer(3, 3, bitdepth=4, palette=[a, b, c, d, e])
        f = BytesIO()
        w.write_array(f, array('B', (4, 3, 2, 3, 2, 0, 2, 0, 1)))
        r = png.Reader(bytes=f.getvalue())
        x, y, pixels, meta = r.asRGBA8()
        self.assertEqual(x, 3)
        self.assertEqual(y, 3)
        c = c + (255,)
        d = d + (255,)
        e = e + (255,)
        boxed = [(e, d, c), (d, c, a), (c, a, b)]
        flat = map(lambda row: itertools.chain(*row), boxed)
        self.assertEqual([list(row) for row in pixels],
                         [list(row) for row in flat])

    def test_RGB_to_RGBA(self):
        """asRGBA8() on colour type 2 source."""
        # Test for Issue 26 (googlecode)
        # Also test that png.Reader can take a "file-like" object.
        r = png.Reader(BytesIO(pngsuite.basn2c08))
        x, y, pixels, meta = r.asRGBA8()
        # Test the pixels at row 9 columns 0 and 1.
        row9 = list(pixels)[9]
        self.assertEqual(list(row9[0:8]),
                         [0xff, 0xdf, 0xff, 0xff, 0xff, 0xde, 0xff, 0xff])

    def test_L_to_RGB(self):
        """asRGB() on grey source."""
        r = png.Reader(bytes=pngsuite.basi0g08)
        x, y, rows, meta = r.asRGB()
        self.assertEqual(meta['planes'], 3)
        row9 = list(list(rows)[9])
        self.assertEqual(row9[0:6],
                         [222, 222, 222, 221, 221, 221])

    def test_L16_to_RGB(self):
        """asRGB() on 16-bit grey source."""
        r = png.Reader(bytes=pngsuite.basi0g16)
        _, _, rows, meta = r.asRGB()
        self.assertEqual(meta['planes'], 3)
        row9 = list(list(rows)[9])
        self.assertEqual(row9[0:6],
                         [4608, 4608, 4608, 6912, 6912, 6912])

    def test_L_to_RGBA(self):
        """asRGBA() on grey source."""
        # Test for Issue 60 (googlecode)
        r = png.Reader(bytes=pngsuite.basi0g08)
        x, y, pixels, meta = r.asRGBA()
        self.assertEqual(meta['planes'], 4)
        row9 = list(list(pixels)[9])
        self.assertEqual(row9[0:8],
                         [222, 222, 222, 255, 221, 221, 221, 255])

    def test_LA_to_RGBA(self):
        """asRGBA() on LA source."""
        r = png.Reader(bytes=pngsuite.basn4a16)
        x, y, rows, meta = r.asRGBA()
        self.assertEqual(meta['planes'], 4)
        row9 = list(list(rows)[9])
        self.assertEqual(
            row9[0:8],
            [38052, 38052, 38052, 0, 36157, 36157, 36157, 4229])

    def test_RGB_trns(self):
        "Test colour type 2 and tRNS chunk."
        # Test for Issue 25 (googlecode)
        r = png.Reader(bytes=pngsuite.tbrn2c08)
        x, y, pixels, meta = r.asRGBA8()
        # I just happen to know that the first pixel is transparent.
        # In particular it should be #7f7f7f00
        row0 = list(pixels)[0]
        self.assertEqual(tuple(row0[0:4]), (0x7f, 0x7f, 0x7f, 0x00))

    def test_interlace_read(self):
        """Adam7 interlace reading.
        For images in the PngSuite that have both
        an interlaced and straightlaced pair,
        test that both images of the pair give the same array of pixels."""
        for candidate in pngsuite.png:
            if not candidate.startswith('basn'):
                continue
            candi = candidate.replace('n', 'i')
            if candi not in pngsuite.png:
                continue
            straight = png.Reader(bytes=pngsuite.png[candidate])
            adam7 = png.Reader(bytes=pngsuite.png[candi])
            # Just compare the pixels.  Ignore x,y (because they're
            # likely to be correct?); metadata is ignored because the
            # "interlace" member differs.  Lame.
            straight = straight.read()[2]
            adam7 = adam7.read()[2]
            self.assertEqual([list(row) for row in straight],
                             [list(row) for row in adam7])

    def test_interlace_write(self):
        """Adam7 interlace writing.
        For each test image in the PngSuite, write an interlaced
        and a straightlaced version.  Decode both, and compare results.
        """
        # Not such a great test, because the only way we can check what
        # we have written is to read it back again.

        for name, bytes in pngsuite.png.items():
            # Only certain colour types supported for this test.
            if name[3:5] not in ['n0', 'n2', 'n4', 'n6']:
                continue
            it = png.Reader(bytes=bytes)
            x, y, pixels, meta = it.read()
            pngi = topngbytes(
                'adam7wn' + name + '.png', pixels,
                x=x, y=y, bitdepth=it.bitdepth,
                greyscale=it.greyscale, alpha=it.alpha,
                transparent=it.transparent,
                interlace=False)
            x, y, ps, meta = png.Reader(bytes=pngi).read()
            it = png.Reader(bytes=bytes)
            x, y, pixels, meta = it.read()
            pngs = topngbytes(
                'adam7wi' + name + '.png', pixels,
                x=x, y=y, bitdepth=it.bitdepth,
                greyscale=it.greyscale, alpha=it.alpha,
                transparent=it.transparent,
                interlace=True)
            x, y, pi, meta = png.Reader(bytes=pngs).read()
            self.assertEqual([list(row) for row in ps],
                             [list(row) for row in pi])

    def test_interlace_write_array_bytes(self):
        """
        Test that when using `write_array` a bytes instance
        can be used.
        As per https://github.com/drj11/pypng/issues/65
        """

        f = BytesIO()
        w = png.Writer(3, 2, interlace=True, greyscale=True)
        w.write_array(f, bytes([0x55, 0xaa, 0xff, 0xaa, 0x55, 0x00]))

    def test_palette_info(self):
        """Test that a palette PNG returns the palette in info."""
        r = png.Reader(bytes=pngsuite.basn3p04)
        x, y, pixels, info = r.read()
        self.assertEqual(x, 32)
        self.assertEqual(y, 32)
        self.assertIn('palette', info)

    def test_read_palette_write(self):
        """Test metadata for paletted PNG can be passed from one PNG
        to another."""
        r = png.Reader(bytes=pngsuite.basn3p04)
        x, y, pixels, info = r.read()
        w = png.Writer(**info)
        o = BytesIO()
        w.write(o, pixels)
        o.flush()
        o.seek(0)
        r = png.Reader(file=o)
        _, _, _, again_info = r.read()
        # Same palette
        self.assertEqual(again_info['palette'], info['palette'])

    def test_deepen_palette(self):
        """Test that palette bitdepth can be increased,
        without change of pixel values."""
        r = png.Reader(bytes=pngsuite.basn3p04)
        x, y, pixels, info = r.read()
        pixels = [list(row) for row in pixels]
        info['bitdepth'] = 8
        w = png.Writer(**info)
        o = BytesIO()
        w.write(o, pixels)
        o.flush()
        o.seek(0)
        r = png.Reader(file=o)
        _, _, again_pixels, again_info = r.read()
        # Same pixels
        again_pixels = [list(row) for row in again_pixels]
        self.assertEqual(again_pixels, pixels)

    def test_palette_force_alpha(self):
        """Test forcing alpha channel for palette."""
        r = png.Reader(bytes=pngsuite.basn3p04)
        r.preamble()
        r.palette(alpha='force')

    def test_L_trns_0(self):
        """Create greyscale image with tRNS chunk."""
        return self.helper_L_trns(0)

    def test_L_trns_tuple(self):
        """Using 1-tuple for transparent arg."""
        return self.helper_L_trns((0,))

    def helper_L_trns(self, transparent):
        """Helper used by :meth:`test_L_trns*`."""
        pixels = zip([0x00, 0x38, 0x4c, 0x54, 0x5c, 0x40, 0x38, 0x00])
        o = BytesIO()
        w = png.Writer(8, 8,
                       greyscale=True, bitdepth=1, transparent=transparent)
        w.write_packed(o, pixels)
        r = png.Reader(bytes=o.getvalue())
        x, y, pixels, meta = r.asDirect()
        self.assertTrue(meta['alpha'])
        self.assertTrue(meta['greyscale'])
        self.assertEqual(meta['bitdepth'], 1)

    def test_read_info_write(self):
        """Test that the dictionary returned by `read`
        can be used as args for :meth:`Writer`.
        """
        r = png.Reader(bytes=pngsuite.basn2c16)
        info = r.read()[3]
        png.Writer(**info)

    def test_write_background_colour(self):
        """Test that background keyword works."""

        w = png.Writer(1, 2, greyscale=False, background=[0x55, 0xFF, 0xAA])
        o = BytesIO()
        w.write(o, [[1, 4, 192], [16, 224, 255]])
        r = png.Reader(bytes=o.getvalue())
        _, _, rows, info = r.asDirect()
        rows = list(rows)
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            [list(row) for row in rows],
            [[1, 4, 192], [16, 224, 255]])

    def test_write_background_grey(self):
        """Test that background keyword works."""

        w = png.Writer(2, 2, alpha=True, background=[0x55])
        o = BytesIO()
        w.write(o, [[1, 255, 4, 192], [16, 0, 224, 255]])
        r = png.Reader(bytes=o.getvalue())
        _, _, rows, info = r.asDirect()
        rows = list(rows)
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            [list(row) for row in rows],
            [[1, 255, 4, 192], [16, 0, 224, 255]])

    def test_write_compression(self):
        """Test that compression keyword works."""

        w = png.Writer(2, 2, compression=1)
        o = BytesIO()
        w.write(o, [[1, 4], [16, 224]])
        r = png.Reader(bytes=o.getvalue())
        x, y, rows, info = r.asDirect()
        rows = list(rows)
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            [list(row) for row in rows],
            [[1, 4], [16, 224]])

    def test_write_packed(self):
        """Test iterator for row when using write_packed.

        Indicative for Issue 47 (googlecode).
        """
        w = png.Writer(16, 2, greyscale=True, alpha=False, bitdepth=1)
        o = BytesIO()
        w.write_packed(o, [itertools.chain([0x0a], [0xaa]),
                           itertools.chain([0x0f], [0xff])])
        r = png.Reader(bytes=o.getvalue())
        x, y, pixels, info = r.asDirect()
        pixels = list(pixels)
        self.assertEqual(len(pixels), 2)
        self.assertEqual(len(pixels[0]), 16)

    def test_interlaced_array(self):
        """Reading an interlaced PNG yields each row as an array."""
        r = png.Reader(bytes=pngsuite.basi0g08)
        list(r.read()[2])[0].tostring

    def test_trns_array(self):
        """A type 2 PNG with tRNS chunk yields each row
        as an array (using asDirect)."""
        r = png.Reader(bytes=pngsuite.tbrn2c08)
        list(r.asDirect()[2])[0].tostring

    def test_flat(self):
        """Test read_flat."""
        import hashlib

        r = png.Reader(bytes=pngsuite.basn0g02)
        x, y, pixel, meta = r.read_flat()
        d = hashlib.md5(seq_to_bytes(pixel)).hexdigest()
        self.assertEqual(d, '255cd971ab8cd9e7275ff906e5041aa0')

    def test_no_phys_chunk(self):
        """
        Check that no pHYs chunk when not asked.
        """
        width = height = 3
        pixels = [[0] * width] * height
        out = BytesIO()
        # = Check if pHYs chunk is omitted by default
        writer = png.Writer(width=width, height=height, greyscale=True)
        writer.write(out, pixels)
        out.seek(0)
        self.assertNotIn(b'pHYs', out.getvalue())
        out.seek(0)
        reader = png.Reader(file=out)
        w, h, _, meta = reader.read()
        self.assertNotIn('physical', meta)
        self.assertFalse(hasattr(reader, 'x_pixels_per_unit'))

    def test_phys_chunk(self):
        """
        Check that pHYs chunk is generated.
        """
        width = height = 3
        pixels = [[0] * width] * height
        out = BytesIO()
        writer = png.Writer(width=width, height=height, greyscale=True,
                            x_pixels_per_unit=2000,
                            y_pixels_per_unit=1000,
                            unit_is_meter=True)
        writer.write(out, pixels)
        out.seek(0)
        reader = png.Reader(file=out)
        w, h, _, meta = reader.read()
        self.assertIn('physical', meta)
        self.assertEqual(2000, reader.x_pixels_per_unit)
        self.assertEqual(1000, reader.y_pixels_per_unit)
        self.assertTrue(reader.unit_is_meter)
        expected = (2000, 1000, True)
        self.assertEqual(expected, meta['physical'])
        res = meta['physical']
        self.assertEqual(2000, res.x)
        self.assertEqual(1000, res.y)
        self.assertTrue(res.unit_is_meter)

    def test_phys_chunk_2(self):
        """
        Check pHYs chunk when unit_is_meter is False.
        """
        width = height = 3
        pixels = [[0] * width] * height
        out = BytesIO()
        writer = png.Writer(width=width, height=height, greyscale=True,
                            x_pixels_per_unit=2, y_pixels_per_unit=1,
                            unit_is_meter=False)
        writer.write(out, pixels)
        out.seek(0)
        reader = png.Reader(file=out)
        w, h, _, meta = reader.read()
        self.assertIn('physical', meta)
        self.assertEqual(2, reader.x_pixels_per_unit)
        self.assertEqual(1, reader.y_pixels_per_unit)
        self.assertFalse(reader.unit_is_meter)
        expected = (2, 1, False)
        self.assertEqual(expected, meta['physical'])
        res = meta['physical']
        self.assertEqual(2, res.x)
        self.assertEqual(1, res.y)
        self.assertFalse(res.unit_is_meter)

    def test_chunk_after_idat(self):
        """
        Test with a PNG that has an ancillary chunk after IDAT chunks.
        For coverage.
        """
        k = 'f02n0g08'
        reader = png.Reader(bytes=pngsuite.png[k])
        text_chunk = (b'tEXt', b'Comment\x00Test chunk follows IDAT')

        def more_chunks():
            for t, v in reader.chunks():
                if t == b'IEND':
                    yield text_chunk
                yield t, v

        o = BytesIO()
        png.write_chunks(o, more_chunks())

        reader = png.Reader(bytes=o.getvalue())
        _, _, rows, info = reader.read()
        list(rows)

    def test_plte_bkgd(self):
        """
        Test colortype 3 PNG with bKGD chunk.
        For coverage.
        """
        k = 'basn3p04'
        reader = png.Reader(bytes=pngsuite.png[k])

        def more_chunks():
            for t, v in reader.chunks():
                yield t, v
                if t == b'PLTE':
                    yield b'bKGD', b'\x00'

        o = BytesIO()
        png.write_chunks(o, more_chunks())

        reader = png.Reader(bytes=o.getvalue())
        _, _, rows, info = reader.read()
        list(rows)

    def test_modify_rows(self):
        """Tests that the rows yielded by the pixels generator
        can be safely modified.
        """
        k = 'f02n0g08'
        r1 = png.Reader(bytes=pngsuite.png[k])
        r2 = png.Reader(bytes=pngsuite.png[k])
        _, _, pixels1, info1 = r1.asDirect()
        _, _, pixels2, info2 = r2.asDirect()
        izip = getattr(itertools, 'izip', zip)
        for row1, row2 in izip(pixels1, pixels2):
            self.assertEqual(row1, row2)
            for i in range(len(row1)):
                row1[i] = 11117 % (i + 1)

    def test_cannot_length_check(self):
        """
        The length check cannot be used on an itertools.chain object.
        For coverage.
        """
        rows = [itertools.chain([0, 0xaa], [0x55, 0xff])]
        w = png.Writer(size=(4, 1))
        w.write(BytesIO(), rows)

    # Invalid file format tests.  These construct various badly
    # formatted PNG files, then feed them into a Reader.  When
    # everything is working properly, we should get FormatError
    # exceptions raised.

    def test_empty(self):
        """Test empty file."""

        r = png.Reader(bytes=b'')
        self.assertRaises(png.FormatError, r.asDirect)

    def test_signature_only(self):
        """Test file containing just signature bytes."""

        r = png.Reader(bytes=pngsuite.basi0g01[:8])
        self.assertRaises(png.FormatError, r.asDirect)

    def test_chunk_truncated(self):
        """
        Chunk doesn't have length and type.
        """
        r = png.Reader(bytes=pngsuite.basi0g01[:13])
        try:
            r.asDirect()
        except Exception as e:
            self.assertIsInstance(e, png.FormatError)
            self.assertIn('chunk length', str(e))

    def test_chunk_short(self):
        """
        Chunk that is too short.
        """
        r = png.Reader(bytes=pngsuite.basi0g01[:21])
        try:
            r.asDirect()
        except Exception as e:
            self.assertIsInstance(e, png.FormatError)
            self.assertIn('too short', str(e))

    def test_no_checksum(self):
        """
        Chunk that's too small to contain a checksum.
        """
        r = png.Reader(bytes=pngsuite.basi0g01[:29])
        try:
            r.asDirect()
        except Exception as e:
            self.assertIsInstance(e, png.FormatError)
            self.assertIn('checksum', str(e))

    def test_checksum_bad(self):
        """
        Chunk has bad checksum.
        """
        bad_png = bytearray(pngsuite.basi0g01)
        bad_png[30] = 1
        r = png.Reader(bytes=bad_png)
        try:
            r.read()
        except Exception as e:
            self.assertIsInstance(e, png.FormatError)
            self.assertIn('hecksum error', str(e))

    def test_type_bad(self):
        """
        Chunk has bad type.
        """
        bad_png = bytearray(pngsuite.basi0g01)
        bad_png[15] |= 0x80
        r = png.Reader(bytes=bad_png)
        try:
            r.read()
        except Exception as e:
            self.assertIsInstance(e, png.FormatError)
            self.assertIn('invalid Chunk', str(e))

    def test_ihdr_length(self):
        """Test file that has wrong length IHDR."""

        def change_ihdr_length(chunk):
            if chunk[0] != b'IHDR':
                return chunk
            data = chunk[1]
            data += b'garbage'
            chunk = (chunk[0], data)
            return chunk
        self.assertRaises(
            png.FormatError,
            read_modify_chunks,
            change_ihdr_length)

    def test_ihdr_compression(self):
        """Test file that has invalid compression IHDR value."""

        def change_ihdr_compression(chunk):
            if chunk[0] != b'IHDR':
                return chunk
            data = chunk[1]
            data = data[:10] + b'\x80' + data[11:]
            chunk = (chunk[0], data)
            return chunk
        self.assertRaises(
            png.FormatError,
            read_modify_chunks,
            change_ihdr_compression)

    def test_ihdr_interlace(self):
        """Test file that has invalid interlace IHDR value."""

        def change_ihdr_interlace(chunk):
            if chunk[0] != b'IHDR':
                return chunk
            data = chunk[1]
            data = data[:12] + b'\x80'
            chunk = (chunk[0], data)
            return chunk
        self.assertRaises(
            png.FormatError,
            read_modify_chunks,
            change_ihdr_interlace)

    def test_ihdr_filter(self):
        """Test file that has invalid filter IHDR value."""

        def change_ihdr_filter(chunk):
            if chunk[0] != b'IHDR':
                return chunk
            data = chunk[1]
            data = data[:11] + b'\x80' + data[12:]
            chunk = (chunk[0], data)
            return chunk
        self.assertRaises(
            png.FormatError,
            read_modify_chunks,
            change_ihdr_filter)

    def test_iend_missing(self):
        """Test file with missing IEND chunk."""
        r = png.Reader(bytes=pngsuite.basn0g02[:-12])
        _, _, rows, info = r.read()
        self.assertRaises(
            png.ChunkError,
            list,
            rows)

    def test_extra_pixels(self):
        """Test file that contains too many pixels."""

        def add_garbage(chunk):
            if chunk[0] != b'IDAT':
                return chunk
            data = zlib.decompress(chunk[1])
            data += b'\x00garbage'
            data = zlib.compress(data)
            chunk = (chunk[0], data)
            return chunk
        self.assertRaises(png.FormatError, read_modify_chunks, add_garbage)

    def test_lack_pixels(self):
        """Test file that contains too few pixels."""

        def truncate_idat(chunk):
            if chunk[0] != b'IDAT':
                return chunk
            # Remove last byte.
            data = zlib.decompress(chunk[1])
            data = data[:-1]
            data = zlib.compress(data)
            return (chunk[0], data)
        self.assertRaises(png.FormatError, read_modify_chunks, truncate_idat)

    def test_bad_filter(self):
        """Test file that contains impossible filter type."""

        def corrupt_filter(chunk):
            if chunk[0] != b'IDAT':
                return chunk
            data = zlib.decompress(chunk[1])
            # Corrupt the first filter byte
            data = b'\x99' + data[1:]
            data = zlib.compress(data)
            return (chunk[0], data)
        self.assertRaises(png.FormatError, read_modify_chunks, corrupt_filter)

    # from_array

    def test_from_array_L(self):
        img = png.from_array([[0, 0x33, 0x66], [0xff, 0xcc, 0x99]], 'L')
        img.write(BytesIO())

    def test_from_array_L16(self):
        img = png.from_array(group(range(2**16), 256), 'L;16')
        img.write(BytesIO())

    def test_from_array_RGB(self):
        img = png.from_array([[0, 0, 0,
                               0, 0, 1,
                               0, 1, 0,
                               0, 1, 1],
                             [1, 0, 0,
                              1, 0, 1,
                              1, 1, 0,
                              1, 1, 1]], 'RGB;1')
        o = BytesIO()
        img.write(o)

    def test_from_array_iterator(self):
        i = itertools.islice(itertools.count(10), 20)
        i = ([x, x, x] for x in i)
        img = png.from_array(i, 'RGB;5', dict(height=20))
        f = BytesIO()
        img.write(f)

    def test_from_array_bad(self):
        """Invoke from_array incorrectly to provoke Error."""
        self.assertRaises(
            png.Error,
            png.from_array,
            [[1]], 'gray')

    def test_from_array_L2(self):
        png.from_array([[0, 1], [2, 3]], 'L2').write(BytesIO())

    def test_from_array_width(self):
        """
        Test width argument.
        For coverage.
        """
        img = png.from_array(
            [[0, 0x33, 0x66], [0xff, 0xcc, 0x99]],
            'L',
            info=dict(size=(3, 2))
            )
        img.write(BytesIO())

    def test_from_array_LA(self):
        png.from_array([[3, 1], [0, 3]], 'LA2',
                       info=dict(greyscale=True)).write(BytesIO())

    def test_from_array_LA_alpha_bad(self):
        self.assertRaises(
            png.ProtocolError,
            png.from_array,
            [[3, 1], [0, 3]],
            'LA2',
            info=dict(greyscale=True, alpha=False))

    def test_from_array_LA_grey_bad(self):
        self.assertRaises(
            png.ProtocolError,
            png.from_array,
            [[3, 1], [0, 3]],
            'LA2',
            info=dict(greyscale=False, alpha=True))

    def test_from_array_LA_bitdepth_bad(self):
        self.assertRaises(
            png.ProtocolError,
            png.from_array,
            [[3, 1], [0, 3]],
            'LA2',
            info=dict(bitdepth=4))

    def test_from_array_iterator_height(self):
        """Row iterator without height raises Error."""
        i = itertools.islice(itertools.count(10), 20)
        i = ([x, x, x] for x in i)
        self.assertRaises(
            png.ProtocolError,
            png.from_array,
            i,
            'RGB;5')

# numpy dependent tests.

    def test_numpy_uint16(self):
        """numpy uint16."""

        numpy or self.skipTest("numpy is not available")

        rows = [[numpy.uint16(x) for x in range(0, 0x10000, 0x5555)]]
        topngbytes('numpyuint16.png', rows, 4, 1,
                   greyscale=True, alpha=False, bitdepth=16)

    def test_numpy_uint8(self):
        """numpy uint8."""

        numpy or self.skipTest("numpy is not available")

        rows = [[numpy.uint8(x) for x in range(0, 0x100, 0x55)]]
        topngbytes('numpyuint8.png', rows, 4, 1,
                   greyscale=True, alpha=False, bitdepth=8)

    def test_numpy_bool(self):
        """numpy bool."""

        numpy or self.skipTest("numpy is not available")

        rows = numpy.array([[0, 1]], dtype=bool)
        img = png.from_array(rows, 'L')
        assert img.info['bitdepth'] == 1

    def test_numpy_array(self):
        """numpy array."""

        numpy or self.skipTest("numpy is not available")

        pixels = numpy.array([[0, 0x5555], [0x5555, 0xaaaa]], numpy.uint16)
        img = png.from_array(pixels, 'L')
        img.write(BytesIO())

    def test_numpy_tranpose(self):
        """Transposed numpy array (works when copied)."""

        # See https://github.com/drj11/pypng/issues/91

        numpy or self.skipTest("numpy is not available")

        a = numpy.array([[0, 0x55], [0x55, 0xaa]], numpy.uint8)
        # I assert it's a bug in numpy that the copy is required here.
        # But while it is required, I may as well test that it does work.
        aT = numpy.transpose(a).copy()
        img = png.from_array(aT, mode='L')
        img.write(BytesIO())

    def test_numpy_palette(self):
        """numpy palette."""

        numpy or self.skipTest("numpy is not available")

        s = ['110010010011',
             '101011010100',
             '110010110101',
             '100010010011']

        s = [[int(p) for p in row] for row in s]

        palette = [(0x55, 0x55, 0x55), (0xff, 0x99, 0x99)]
        # Creates a 2x3 array
        pnp = numpy.array(palette)
        png.Writer(len(s[0]), len(s), palette=pnp, bitdepth=1)

    # Filters and unfilters

    def test_undo_filter(self):
        reader = png.Reader(bytes=b'')
        reader.psize = 3
        scanprev = array('B', [20, 21, 22, 210, 211, 212])
        scanline = array('B', [30, 32, 34, 230, 233, 236])

        def cp(a):
            return array('B', a)

        # none
        out = reader.undo_filter(0, cp(scanline), cp(scanprev))
        self.assertEqual(list(out), list(scanline))
        # sub
        out = reader.undo_filter(1, cp(scanline), cp(scanprev))
        self.assertEqual(list(out), [30, 32, 34, 4, 9, 14])
        # up
        out = reader.undo_filter(2, cp(scanline), cp(scanprev))
        self.assertEqual(list(out), [50, 53, 56, 184, 188, 192])
        # average
        out = reader.undo_filter(3, cp(scanline), cp(scanprev))
        self.assertEqual(list(out), [40, 42, 45, 99, 103, 108])
        # paeth
        out = reader.undo_filter(4, cp(scanline), cp(scanprev))
        self.assertEqual(list(out), [50, 53, 56, 184, 188, 192])

    def test_undo_filter_paeth(self):
        """Edge cases for undoing paeth filter."""
        reader = png.Reader(bytes=b'')
        reader.psize = 3
        scanprev = array('B', [2, 0, 0, 0, 9, 11])
        scanline = array('B', [6, 10, 9, 100, 101, 102])

        out = reader.undo_filter(4, scanline, scanprev)
        self.assertEqual(list(out), [8, 10, 9, 108, 111, 113])

    # Generally, protocol errors

    def test_row_length_bad(self):
        # See https://github.com/drj11/pypng/issues/28
        writer = png.Writer(width=4, height=1, greyscale=True)
        o = BytesIO()

        self.assertRaises(png.ProtocolError,
                          writer.write,
                          o, [[1, 111, 222]])

    def test_size_length_bad(self):
        """
        Wrong tuple length in size keyword.
        """
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            size=(2, 2, 3))

    def test_width_bad(self):
        """Wrong width in constructor."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            width=3, size=(2, 3))

    def test_height_bad(self):
        """Wrong height in constructor."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            height=3, size=(3, 2))

    def test_background_bad(self):
        """Wrong background in constructor."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            size=(2, 2),
            background=[0x55, 0x55, 0x55])

    def test_background_unnatural(self):
        """non-integer background in constructor."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            size=(2, 2),
            background=[0.5])

    def test_background_rgb_unnatural(self):
        """non-integer background in constructor."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            size=(2, 2),
            greyscale=False,
            background=[1, 1, 0.5])

    def test_alpha_trns(self):
        """alpha and transparent don't mix."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            size=(2, 2),
            alpha=True,
            transparent=[1])

    def test_bitdepth_bad(self):
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            size=(2, 2),
            bitdepth=0)

    def test_write_palette_big(self):
        """Palette too big should raise error."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, bitdepth=2, palette=_palette3*86)

    def test_write_palette_bad_tuples(self):
        """Palette with incorrect size tuples should raise error."""
        a, b, c = _palette3
        # Corrupt c by shortening it.
        c = c[:2]
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, bitdepth=2, palette=[a, b, c])

    def test_write_palette_bad_transparency(self):
        """Palette with transparent entries following opaque ones."""
        a = (255, 255, 255, 255)
        b = (200, 120, 120)
        c = (50, 99, 50, 50)
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, bitdepth=2, palette=[a, b, c])

    def test_wrong_rows(self):
        """
        Wrong number of rows.
        """
        rows = [[0, 0xaa], [0x55, 0xff]]
        w = png.Writer(size=(2, 1))
        self.assertRaises(
            png.ProtocolError,
            w.write,
            BytesIO(),
            rows)

    def test_write_palette_bad_fraction(self):
        """Palette with fractions should raise error."""
        a = (255, 255, 255, 0.9)
        b = (200, 120, 120)
        c = (50, 99, 50)
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, bitdepth=2, palette=[a, b, c])

    def test_palette_bitdepths(self):
        """Palette is incompatible with multiple bitdepths."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, bitdepth=(2, 2), palette=_palette3)

    def test_palette_bitdepth_wrong(self):
        """Palette is incompatible with some bitdepths."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, bitdepth=7, palette=_palette3)

    def test_palette_transparent(self):
        """Palette is incompatible with transarent."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, palette=_palette3, transparent=(9,))

    def test_palette_alpha(self):
        """Palette is incompatible with alpha."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, palette=_palette3, alpha=True)

    def test_palette_greyscale(self):
        """Palette is incompatible with greyscale."""
        self.assertRaises(
            png.ProtocolError,
            png.Writer,
            1, 4, palette=_palette3, greyscale=True)

    def test_writer_noargs(self):
        """Invoking Writer with no args should raise error."""
        self.assertRaises(png.ProtocolError, png.Writer)

    def test_writer_width_bad(self):
        """Invoking Writer with bad width should raise error."""
        self.assertRaises(png.ProtocolError, png.Writer, 0, 4)

    def test_writer_height_bad(self):
        """Invoking Writer with bad height should raise error."""
        self.assertRaises(png.ProtocolError, png.Writer, -4, 4)

    def test_writer_width_big(self):
        """Invoking Writer with big width should raise error."""
        self.assertRaises(png.ProtocolError, png.Writer, 2**31, 4)

    def test_writer_height_big(self):
        """Invoking Writer with big height should raise error."""
        self.assertRaises(png.ProtocolError, png.Writer, 4, 2**31)

    # scripts in test directory

    def test_test_dir(self):
        runs = []
        for path in sorted(glob.glob('test/*')):
            if not os.access(path, os.X_OK):
                # Skip non-executables (probably fixtures?)
                continue
            status = os.system(path)
            runs.append((path, status))
        failed_runs = [run for run in runs if run[1]]
        self.assertTrue(
            len(failed_runs) == 0,
            msg="%r failed" % failed_runs)


def read_modify_chunks(modify_chunk):
    """Create a temporary PNG file by modifying the chunks of
    an existing one, then read that temporary file.
    Each chunk is passed through the function `modify_chunk`.
    """

    r = png.Reader(bytes=pngsuite.basn0g01)
    o = BytesIO()

    def newchunks():
        for chunk in r.chunks():
            yield modify_chunk(chunk)

    png.write_chunks(o, newchunks())
    r = png.Reader(bytes=o.getvalue())
    return list(r.asDirect()[2])


def group(s, n):
    return list(zip(* [iter(s)] * n))


if __name__ == '__main__':
    unittest.main(__name__)
