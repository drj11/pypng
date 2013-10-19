# This file comprises the tests that are internally validated (as
# opposed to tests which produce output files that are externally
# validated).  Primarily they are unittests.

# Note that it is difficult to internally validate the results of
# writing a PNG file.  The only thing we can do is read it back in
# again, which merely checks consistency, not that the PNG file we
# produce is valid.

# Run the tests from the command line:
#   python -c 'import test_png;test_png.runTest()'
# If you have nose installed you can use that:
#   nosetests .

# (For an in-memory binary file IO object) We use BytesIO where
# available, otherwise we use StringIO, but name it BytesIO.
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO
import itertools
import struct
# http://www.python.org/doc/2.4.4/lib/module-unittest.html
import unittest
import zlib

from array import array

import png
import pngsuite
import sys

from png import strtobytes      # Don't do this at home.


def runTest():
    unittest.main(__name__)

def topngbytes(name, rows, x, y, **k):
    """
    Convenience function for creating a PNG file "in memory" as
    a string.  Creates a :class:`Writer` instance using the keyword
    arguments, then passes `rows` to its :meth:`Writer.write` method.
    The resulting PNG file is returned as a string.  `name` is used
    to identify the file for debugging.
    """

    import os

    print name
    f = BytesIO()
    w = png.Writer(x, y, **k)
    w.write(f, rows)
    if os.environ.get('PYPNG_TEST_TMP'):
        w = open(name, 'wb')
        w.write(f.getvalue())
        w.close()
    return f.getvalue()

def _redirect_io(inp, out, f):
    """Calls the function `f` with ``sys.stdin`` changed to `inp`
    and ``sys.stdout`` changed to `out`.  They are restored when `f`
    returns.  This function returns whatever `f` returns.
    """

    import os
    import sys

    oldin, sys.stdin = sys.stdin, inp
    oldout, sys.stdout = sys.stdout, out
    try:
        x = f()
    finally:
        sys.stdin = oldin
        sys.stdout = oldout
    if os.environ.get('PYPNG_TEST_TMP') and hasattr(out,'getvalue'):
        name = mycallersname()
        if name:
            w = open(name+'.png', 'wb')
            w.write(out.getvalue())
            w.close()
    return x

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
    frame_,filename_,lineno_,funname,linelist_,listi_ = (
      inspect.getouterframes(frame)[2])
    return funname

def seqtobytes(s):
    """Convert a sequence of integers to a *bytes* instance.  Good for
    plastering over Python 2 / Python 3 cracks.
    """

    return strtobytes(''.join(chr(x) for x in s))

class Test(unittest.TestCase):
    # This member is used by the superclass.  If we don't define a new
    # class here then when we use self.assertRaises() and the PyPNG code
    # raises an assertion then we get no proper traceback.  I can't work
    # out why, but defining a new class here means we get a proper
    # traceback.
    class failureException(Exception):
        pass

    def helperLN(self, n):
        mask = (1 << n) - 1
        # Use small chunk_limit so that multiple chunk writing is
        # tested.  Making it a test for Issue 20.
        w = png.Writer(15, 17, greyscale=True, bitdepth=n, chunk_limit=99)
        f = BytesIO()
        w.write_array(f, array('B', map(mask.__and__, range(1, 256))))
        r = png.Reader(bytes=f.getvalue())
        x,y,pixels,meta = r.read()
        self.assertEqual(x, 15)
        self.assertEqual(y, 17)
        self.assertEqual(list(itertools.chain(*pixels)),
                         map(mask.__and__, range(1,256)))
    def testL8(self):
        return self.helperLN(8)
    def testL4(self):
        return self.helperLN(4)
    def testL2(self):
        "Also tests asRGB8."
        w = png.Writer(1, 4, greyscale=True, bitdepth=2)
        f = BytesIO()
        w.write_array(f, array('B', range(4)))
        r = png.Reader(bytes=f.getvalue())
        x,y,pixels,meta = r.asRGB8()
        self.assertEqual(x, 1)
        self.assertEqual(y, 4)
        for i,row in enumerate(pixels):
            self.assertEqual(len(row), 3)
            self.assertEqual(list(row), [0x55*i]*3)
    def testP2(self):
        "2-bit palette."
        a = (255,255,255)
        b = (200,120,120)
        c = (50,99,50)
        w = png.Writer(1, 4, bitdepth=2, palette=[a,b,c])
        f = BytesIO()
        w.write_array(f, array('B', (0,1,1,2)))
        r = png.Reader(bytes=f.getvalue())
        x,y,pixels,meta = r.asRGB8()
        self.assertEqual(x, 1)
        self.assertEqual(y, 4)
        self.assertEqual(map(list, pixels), map(list, [a, b, b, c]))
    def testPtrns(self):
        "Test colour type 3 and tRNS chunk (and 4-bit palette)."
        a = (50,99,50,50)
        b = (200,120,120,80)
        c = (255,255,255)
        d = (200,120,120)
        e = (50,99,50)
        w = png.Writer(3, 3, bitdepth=4, palette=[a,b,c,d,e])
        f = BytesIO()
        w.write_array(f, array('B', (4, 3, 2, 3, 2, 0, 2, 0, 1)))
        r = png.Reader(bytes=f.getvalue())
        x,y,pixels,meta = r.asRGBA8()
        self.assertEqual(x, 3)
        self.assertEqual(y, 3)
        c = c+(255,)
        d = d+(255,)
        e = e+(255,)
        boxed = [(e,d,c),(d,c,a),(c,a,b)]
        flat = map(lambda row: itertools.chain(*row), boxed)
        self.assertEqual(map(list, pixels), map(list, flat))
    def testRGBtoRGBA(self):
        "asRGBA8() on colour type 2 source."""
        # Test for Issue 26
        # Also test that png.Reader can take a "file-like" object.
        r = png.Reader(BytesIO(pngsuite.basn2c08))
        x,y,pixels,meta = r.asRGBA8()
        # Test the pixels at row 9 columns 0 and 1.
        row9 = list(pixels)[9]
        self.assertEqual(list(row9[0:8]),
                         [0xff, 0xdf, 0xff, 0xff, 0xff, 0xde, 0xff, 0xff])

        # More testing: rescale and bitdepth > 8
        r = png.Reader(BytesIO(pngsuite.basn2c16))
        x, y, pixels, meta = r.asRGBA8()
        # Test the pixels at row 9 columns 0 and 1.
        row9 = list(pixels)[9]
        self.assertEqual(list(row9[0:8]),
                         [255, 181, 0, 255, 247, 181, 0, 255])

    def testLtoRGBA(self):
        "asRGBA() on grey source."""
        # Test for Issue 60
        r = png.Reader(bytes=pngsuite.basi0g08)
        x,y,pixels,meta = r.asRGBA()
        row9 = list(list(pixels)[9])
        self.assertEqual(row9[0:8],
          [222, 222, 222, 255, 221, 221, 221, 255])
    def testCtrns(self):
        "Test colour type 2 and tRNS chunk."
        # Test for Issue 25
        r = png.Reader(bytes=pngsuite.tbrn2c08)
        x,y,pixels,meta = r.asRGBA8()
        # I just happen to know that the first pixel is transparent.
        # In particular it should be #7f7f7f00
        row0 = list(pixels)[0]
        self.assertEqual(tuple(row0[0:4]), (0x7f, 0x7f, 0x7f, 0x00))
    def testAdam7read(self):
        """Adam7 interlace reading.
        Specifically, test that for images in the PngSuite that
        have both an interlaced and straightlaced pair that both
        images from the pair produce the same array of pixels."""
        for candidate in pngsuite.png:
            if not candidate.startswith('basn'):
                continue
            candi = candidate.replace('n', 'i')
            if candi not in pngsuite.png:
                continue
            print 'adam7 read', candidate
            straight = png.Reader(bytes=pngsuite.png[candidate])
            adam7 = png.Reader(bytes=pngsuite.png[candi])
            # Just compare the pixels.  Ignore x,y (because they're
            # likely to be correct?); metadata is ignored because the
            # "interlace" member differs.  Lame.
            straight = straight.read()[2]
            adam7 = adam7.read()[2]
            self.assertEqual(map(list, straight), map(list, adam7))

    def testAdam7write(self):
        """Adam7 interlace writing.
        For each test image in the PngSuite, write an interlaced
        and a straightlaced version.  Decode both, and compare results.
        """
        # Not such a great test, because the only way we can check what
        # we have written is to read it back again.
        for filtertype in (0, 1, 2, 3, 4,\
                           {'name': 'sum'},\
                           {'name': 'entropy'}):
            for name, bytes_ in pngsuite.png.iteritems():
                # Only certain colour types supported for this test.
                if name[3:5] not in ['n0', 'n2', 'n4', 'n6']:
                    continue
                it = png.Reader(bytes=bytes_)
                x, y, pixels, meta = it.read()
                # straightlaced is easier to filter, so we test interlaced
                # using straight as reference
                pngi = topngbytes('adam7wn' + name + '.png', pixels,
                                  x=x, y=y, bitdepth=it.bitdepth,
                                  greyscale=it.greyscale, alpha=it.alpha,
                                  transparent=it.transparent,
                                  interlace=False, filter_type=0)

                x, y, ps, meta = png.Reader(bytes=pngi).read()
                it = png.Reader(bytes=bytes_)
                x, y, pixels, meta = it.read()
                pngs = topngbytes('adam7wi' + name + '.png', pixels,
                                  x=x, y=y, bitdepth=it.bitdepth,
                                  greyscale=it.greyscale, alpha=it.alpha,
                                  transparent=it.transparent,
                                  interlace=True, filter_type=filtertype)
                x, y, pi, meta = png.Reader(bytes=pngs).read()
                self.assertEqual(map(list, ps), map(list, pi))

    def testPGMin(self):
        """Test that the command line tool can read PGM files."""
        def do():
            return png._main(['testPGMin'])
        s = BytesIO()
        s.write(strtobytes('P5 2 2 3\n'))
        s.write(strtobytes('\x00\x01\x02\x03'))
        s.flush()
        s.seek(0)
        o = BytesIO()
        _redirect_io(s, o, do)
        r = png.Reader(bytes=o.getvalue())
        x,y,pixels,meta = r.read()
        self.assertTrue(r.greyscale)
        self.assertEqual(r.bitdepth, 2)
    def testPAMin(self):
        """Test that the command line tool can read PAM file."""
        def do():
            return png._main(['testPAMin'])
        s = BytesIO()
        s.write(strtobytes('P7\nWIDTH 3\nHEIGHT 1\nDEPTH 4\nMAXVAL 255\n'
                'TUPLTYPE RGB_ALPHA\nENDHDR\n'))
        # The pixels in flat row flat pixel format
        flat =  [255,0,0,255, 0,255,0,120, 0,0,255,30]
        asbytes = seqtobytes(flat)
        s.write(asbytes)
        s.flush()
        s.seek(0)
        o = BytesIO()
        _redirect_io(s, o, do)
        r = png.Reader(bytes=o.getvalue())
        x,y,pixels,meta = r.read()
        self.assertTrue(r.alpha)
        self.assertTrue(not r.greyscale)
        self.assertEqual(list(itertools.chain(*pixels)), flat)
    def testLA4(self):
        """Create an LA image with bitdepth 4."""
        bytes = topngbytes('la4.png', [[5, 12]], 1, 1,
          greyscale=True, alpha=True, bitdepth=4)
        sbit = png.Reader(bytes=bytes).chunk('sBIT')[1]
        self.assertEqual(sbit, strtobytes('\x04\x04'))
    def testPal(self):
        """Test that a palette PNG returns the palette in info."""
        r = png.Reader(bytes=pngsuite.basn3p04)
        x,y,pixels,info = r.read()
        self.assertEqual(x, 32)
        self.assertEqual(y, 32)
        self.assertTrue('palette' in info)
    def testPalWrite(self):
        """Test metadata for paletted PNG can be passed from one PNG
        to another."""
        r = png.Reader(bytes=pngsuite.basn3p04)
        x,y,pixels,info = r.read()
        w = png.Writer(**info)
        o = BytesIO()
        w.write(o, pixels)
        o.flush()
        o.seek(0)
        r = png.Reader(file=o)
        _,_,_,again_info = r.read()
        # Same palette
        self.assertEqual(again_info['palette'], info['palette'])
    def testPalExpand(self):
        """Test that bitdepth can be used to fiddle with pallete image."""
        r = png.Reader(bytes=pngsuite.basn3p04)
        x,y,pixels,info = r.read()
        pixels = [list(row) for row in pixels]
        info['bitdepth'] = 8
        w = png.Writer(**info)
        o = BytesIO()
        w.write(o, pixels)
        o.flush()
        o.seek(0)
        r = png.Reader(file=o)
        _,_,again_pixels,again_info = r.read()
        # Same pixels
        again_pixels = [list(row) for row in again_pixels]
        self.assertEqual(again_pixels, pixels)

    def testPNMsbit(self):
        """Test that PNM files can generates sBIT chunk."""
        def do():
            return png._main(['testPNMsbit'])
        s = BytesIO()
        s.write(strtobytes('P6 8 1 1\n'))
        for pixel in range(8):
            s.write(struct.pack('<I', (0x4081*pixel)&0x10101)[:3])
        s.flush()
        s.seek(0)
        o = BytesIO()
        _redirect_io(s, o, do)
        r = png.Reader(bytes=o.getvalue())
        sbit = r.chunk('sBIT')[1]
        self.assertEqual(sbit, strtobytes('\x01\x01\x01'))
    def testLtrns0(self):
        """Create greyscale image with tRNS chunk."""
        return self.helperLtrns(0)
    def testLtrns1(self):
        """Using 1-tuple for transparent arg."""
        return self.helperLtrns((0,))
    def helperLtrns(self, transparent):
        """Helper used by :meth:`testLtrns*`."""
        pixels = zip([0x00, 0x38, 0x4c, 0x54, 0x5c, 0x40, 0x38, 0x00])
        o = BytesIO()
        w = png.Writer(8, 8, greyscale=True, bitdepth=1, transparent=transparent)
        w.write_packed(o, pixels)
        r = png.Reader(bytes=o.getvalue())
        x,y,pixels,meta = r.asDirect()
        self.assertTrue(meta['alpha'])
        self.assertTrue(meta['greyscale'])
        self.assertEqual(meta['bitdepth'], 1)
    def testWinfo(self):
        """Test the dictionary returned by a `read` method can be used
        as args for :meth:`Writer`.
        """
        r = png.Reader(bytes=pngsuite.basn2c16)
        info = r.read()[3]
        w = png.Writer(**info)
    def testPackedIter(self):
        """Test iterator for row when using write_packed.

        Indicative for Issue 47.
        """
        w = png.Writer(16, 2, greyscale=True, alpha=False, bitdepth=1)
        o = BytesIO()
        w.write_packed(o, [itertools.chain([0x0a], [0xaa]),
                           itertools.chain([0x0f], [0xff])])
        r = png.Reader(bytes=o.getvalue())
        x,y,pixels,info = r.asDirect()
        pixels = list(pixels)
        self.assertEqual(len(pixels), 2)
        self.assertEqual(len(pixels[0]), 16)
    def testInterlacedArray(self):
        """Test that reading an interlaced PNG yields each row as an
        array."""
        r = png.Reader(bytes=pngsuite.basi0g08)
        list(r.read()[2])[0].tostring
    def testTrnsArray(self):
        """Test that reading a type 2 PNG with tRNS chunk yields each
        row as an array (using asDirect)."""
        r = png.Reader(bytes=pngsuite.tbrn2c08)
        list(r.asDirect()[2])[0].tostring

    # Invalid file format tests.  These construct various badly
    # formatted PNG files, then feed them into a Reader.  When
    # everything is working properly, we should get FormatError
    # exceptions raised.
    def testEmpty(self):
        """Test empty file."""

        r = png.Reader(bytes='')
        self.assertRaises(png.FormatError, r.asDirect)
    def testSigOnly(self):
        """Test file containing just signature bytes."""

        r = png.Reader(bytes=pngsuite.basi0g01[:8])
        self.assertRaises(png.FormatError, r.asDirect)
    def testExtraPixels(self):
        """Test file that contains too many pixels."""

        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            data = zlib.decompress(chunk[1])
            data += strtobytes('\x00garbage')
            data = zlib.compress(data)
            chunk = (chunk[0], data)
            return chunk
        self.assertRaises(png.FormatError, self.helperFormat, eachchunk)
    def testNotEnoughPixels(self):
        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            # Remove last byte.
            data = zlib.decompress(chunk[1])
            data = data[:-1]
            data = zlib.compress(data)
            return (chunk[0], data)
        self.assertRaises(png.FormatError, self.helperFormat, eachchunk)
    def helperFormat(self, f):
        r = png.Reader(bytes=pngsuite.basn0g01)
        o = BytesIO()
        def newchunks():
            for chunk in r.chunks():
                yield f(chunk)
        png.write_chunks(o, newchunks())
        r = png.Reader(bytes=o.getvalue())
        return list(r.asDirect()[2])
    def testBadFilter(self):
        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            data = zlib.decompress(chunk[1])
            # Corrupt the first filter byte
            data = strtobytes('\x99') + data[1:]
            data = zlib.compress(data)
            return (chunk[0], data)
        self.assertRaises(png.FormatError, self.helperFormat, eachchunk)

    def testFlat(self):
        """Test read_flat."""

        try:
            from hashlib import md5 as md5_func
        except ImportError:
            # On Python 2.4 there is no hashlib,
            # but there is special module for md5
            import md5

            def md5_func(string):
                m = md5.new()
                m.update(string)
                return m

        r = png.Reader(bytes=pngsuite.basn0g02)
        x,y,pixel,meta = r.read_flat()
        d = md5_func(seqtobytes(pixel)).hexdigest()
        self.assertEqual(d, '255cd971ab8cd9e7275ff906e5041aa0')
    def testfromarray(self):
        img = png.from_array([[0, 0x33, 0x66], [0xff, 0xcc, 0x99]], 'L')
        img.save(BytesIO())
    def testfromarrayL16(self):
        img = png.from_array(group(range(2**16), 256), 'L;16')
        img.save(BytesIO())
    def testfromarrayRGB(self):
        img = png.from_array([[0,0,0, 0,0,1, 0,1,0, 0,1,1],
                          [1,0,0, 1,0,1, 1,1,0, 1,1,1]], 'RGB;1')
        o = BytesIO()
        img.save(o)
    def testfromarrayIter(self):
        import itertools

        i = itertools.islice(itertools.count(10), 20)
        i = itertools.imap(lambda x: [x, x, x], i)
        img = png.from_array(i, 'RGB;5', dict(height=20))
        f = BytesIO()
        img.save(f)

    # numpy dependent tests.  These are skipped (with a message to
    # sys.stderr) if numpy cannot be imported.
    def testNumpyuint16(self):
        """numpy uint16."""

        try:
            import numpy
        except ImportError:
            print >>sys.stderr, "skipping numpy test"
            return

        rows = [map(numpy.uint16, range(0,0x10000,0x5555))]
        b = topngbytes('numpyuint16.png', rows, 4, 1,
            greyscale=True, alpha=False, bitdepth=16)
    def testNumpyuint8(self):
        """numpy uint8."""

        try:
            import numpy
        except ImportError:
            print >>sys.stderr, "skipping numpy test"
            return

        rows = [map(numpy.uint8, range(0,0x100,0x55))]
        b = topngbytes('numpyuint8.png', rows, 4, 1,
            greyscale=True, alpha=False, bitdepth=8)
    def testNumpybool(self):
        """numpy bool."""

        try:
            import numpy
        except ImportError:
            print >>sys.stderr, "skipping numpy test"
            return

        rows = [map(numpy.bool, [0,1])]
        b = topngbytes('numpybool.png', rows, 2, 1,
            greyscale=True, alpha=False, bitdepth=1)
    def testNumpyarray(self):
        """numpy array."""
        try:
            import numpy
        except ImportError:
            print >>sys.stderr, "skipping numpy test"
            return

        pixels = numpy.array([[0,0x5555],[0x5555,0xaaaa]], numpy.uint16)
        img = png.from_array(pixels, 'L')
        img.save('testnumpyL16.png')

    def paeth(self, x, a, b, c):
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
        return x - pr

    # test filters and unfilters
    def testFilterScanlineFirstLine(self):
        line = array('B', [30, 31, 32, 230, 231, 232])
        filter_ = png.Filter(24, prev=None)
        res = filter_.filter_all(line)

        # none
        self.assertEqual(list(res[0]), [0, 30, 31, 32, 230, 231, 232])
        # sub
        self.assertEqual(list(res[1]), [1, 30, 31, 32, 200, 200, 200])
        # up
        self.assertEqual(list(res[2]), [2, 30, 31, 32, 230, 231, 232])
        # average  ! Note that order in list is not equal to filter number
        self.assertEqual(list(res[4]), [3, 30, 31, 32, 215, 216, 216])
        # paeth    ! Note that order in list is not equal to filter number
        self.assertEqual(list(res[3]), [
            4, self.paeth(30, 0, 0, 0), self.paeth(31, 0, 0, 0),
            self.paeth(32, 0, 0, 0), self.paeth(230, 30, 0, 0),
            self.paeth(231, 31, 0, 0), self.paeth(232, 32, 0, 0)
            ])

    def testFilterScanline(self):
        prev = array('B', [20, 21, 22, 210, 211, 212])
        line = array('B', [30, 32, 34, 230, 233, 236])
        filter_ = png.Filter(24, prev=prev)
        res = filter_.filter_all(line)
        # None
        self.assertEqual(list(res[0]), [0, 30, 32, 34, 230, 233, 236])
        # sub
        self.assertEqual(list(res[1]), [1, 30, 32, 34, 200, 201, 202])
        # up
        self.assertEqual(list(res[2]), [2, 10, 11, 12, 20, 22, 24])
        # average  ! Note that order in list is not equal to filter number
        self.assertEqual(list(res[4]), [3, 20, 22, 23, 110, 112, 113])
        # paeth    ! Note that order in list is not equal to filter number
        self.assertEqual(list(res[3]), [
            4, self.paeth(30, 0, 20, 0), self.paeth(32, 0, 21, 0),
            self.paeth(34, 0, 22, 0), self.paeth(230, 30, 210, 20),
            self.paeth(233, 32, 211, 21), self.paeth(236, 34, 212, 22)
            ])

    def testUnfilterScanline(self):
        scanprev = array('B', [20, 21, 22, 210, 211, 212])
        scanline = array('B', [30, 32, 34, 230, 233, 236])

        def undo_filter(filter_type, line, prev):
            filter_ = png.Filter(24, prev=prev)
            line = array('B', line)
            line.insert(0, filter_type)
            return filter_.undo_filter(line)

        out = undo_filter(0, scanline, scanprev)
        self.assertEqual(list(out), list(scanline))  # none
        out = undo_filter(1, scanline, scanprev)
        self.assertEqual(list(out), [30, 32, 34, 4, 9, 14])  # sub
        out = undo_filter(2, scanline, scanprev)
        self.assertEqual(list(out), [50, 53, 56, 184, 188, 192])  # up
        out = undo_filter(3, scanline, scanprev)
        self.assertEqual(list(out), [40, 42, 45, 99, 103, 108])  # average
        out = undo_filter(4, scanline, scanprev)
        self.assertEqual(list(out), [50, 53, 56, 184, 188, 192])  # paeth

    def testUnfilterScanlinePaeth(self):
        # This tests more edge cases in the paeth unfilter
        scanprev = array('B', [2, 0, 0, 0, 9, 11])
        scanline = array('B', [4, 6, 10, 9, 100, 101, 102])
        filter_ = png.Filter(24, prev=scanprev)

        out = filter_.undo_filter(scanline)
        self.assertEqual(list(out), [8, 10, 9, 108, 111, 113])  # paeth

def group(s, n):
    # See http://www.python.org/doc/2.6/library/functions.html#zip
    return zip(*[iter(s)]*n)
