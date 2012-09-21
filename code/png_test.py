# Use py.test to run these tests
import array
import png


def paeth(x, a, b, c):
    """Returns the paeth predictor of the pixel x width neightbors a, b, c.

    +-+-+
    |c|b|
    +-+-+
    |a|x|
    +-+-+

    See http://www.w3.org/TR/PNG/#9Filter-type-4-Paeth for more details.
    """
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


def test_filter_scanline_first_line():
    fo = 3  # bytes per pixel
    line = [30, 31, 32, 230, 231, 232]
    out = png.filter_scanline(0, line, fo, None)  # none
    assert list(out) == [0, 30, 31, 32, 230, 231, 232]
    out = png.filter_scanline(1, line, fo, None)  # sub
    assert list(out) == [1, 30, 31, 32, 200, 200, 200]
    out = png.filter_scanline(2, line, fo, None)  # up
    # TODO: All filtered scanlines start with a byte indicating the filter
    # algorithm, except "up". Is this a bug?
    assert list(out) == [30, 31, 32, 230, 231, 232]
    out = png.filter_scanline(3, line, fo, None)  # average
    assert list(out) == [3, 30, 31, 32, 215, 216, 216]
    out = png.filter_scanline(4, line, fo, None)  # paeth
    assert list(out) == [
        4, paeth(30, 0, 0, 0), paeth(31, 0, 0, 0), paeth(32, 0, 0, 0),
        paeth(230, 30, 0, 0), paeth(231, 31, 0, 0), paeth(232, 32, 0, 0)
        ]


def test_filter_scanline():
    prev = [20, 21, 22, 210, 211, 212]
    line = [30, 32, 34, 230, 233, 236]
    fo = 3
    out = png.filter_scanline(0, line, fo, prev)  # none
    assert list(out) == [0, 30, 32, 34, 230, 233, 236]
    out = png.filter_scanline(1, line, fo, prev)  # sub
    assert list(out) == [1, 30, 32, 34, 200, 201, 202]
    out = png.filter_scanline(2, line, fo, prev)  # up
    assert list(out) == [2, 10, 11, 12, 20, 22, 24]
    out = png.filter_scanline(3, line, fo, prev)  # average
    assert list(out) == [3, 20, 22, 23, 110, 112, 113]
    out = png.filter_scanline(4, line, fo, prev)  # paeth
    assert list(out) == [
        4, paeth(30, 0, 20, 0), paeth(32, 0, 21, 0), paeth(34, 0, 22, 0),
        paeth(230, 30, 210, 20), paeth(233, 32, 211, 21), paeth(236, 34, 212, 22)
        ]

    
def test_unfilter_scanline():
    reader = png.Reader(bytes='')
    reader.psize = 3
    scanprev = array.array('B', [20, 21, 22, 210, 211, 212])
    scanline = array.array('B', [30, 32, 34, 230, 233, 236])
    def cp(a):
        return array.array('B', a)

    out = reader.undo_filter(0, cp(scanline), cp(scanprev))
    assert list(out) == list(scanline)  # none
    out = reader.undo_filter(1, cp(scanline), cp(scanprev))
    assert list(out) == [30, 32, 34, 4, 9, 14]  # sub
    out = reader.undo_filter(2, cp(scanline), cp(scanprev))
    assert list(out) == [50, 53, 56, 184, 188, 192]  # up
    out = reader.undo_filter(3, cp(scanline), cp(scanprev))
    assert list(out) == [40, 42, 45, 99, 103, 108]  # average
    out = reader.undo_filter(4, cp(scanline), cp(scanprev))
    assert list(out) == [50, 53, 56, 184, 188, 192]  # paeth
    

def test_unfilter_scanline_paeth():
    # This tests more edge cases in the paeth unfilter
    reader = png.Reader(bytes='')
    reader.psize = 3
    scanprev = array.array('B', [2, 0, 0, 0, 9, 11])
    scanline = array.array('B', [6, 10, 9, 100, 101, 102])

    out = reader.undo_filter(4, scanline, scanprev)
    assert list(out) == [8, 10, 9, 108, 111, 113]  # paeth


def arraify(list_of_str):
    return [array.array('B', s) for s in list_of_str]


def test_iterstraight():
    reader = png.Reader(bytes='')
    reader.row_bytes = 6
    reader.psize = 3
    rows = reader.iterstraight(arraify(['\x00abcdef', '\x00ghijkl']))
    assert list(rows) == arraify(['abcdef', 'ghijkl'])

    rows = reader.iterstraight(arraify(['\x00abc', 'def\x00ghijkl']))
    assert list(rows) == arraify(['abcdef', 'ghijkl'])

    rows = reader.iterstraight(arraify(['\x00abcdef\x00ghijkl']))
    assert list(rows) == arraify(['abcdef', 'ghijkl'])

    rows = reader.iterstraight(arraify(['\x00abcdef\x00ghi', 'jkl']))
    assert list(rows) == arraify(['abcdef', 'ghijkl'])
