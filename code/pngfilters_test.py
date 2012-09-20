import array
import pyximport
pyximport.install()
import cpngfilters as pngfilters


def test_unfilter_scanline_paeth():
    # This tests more edge cases in the paeth unfilter
    scanprev = array.array('B', [2, 0, 0, 0, 9, 11])
    scanline = array.array('B', [6, 10, 9, 100, 101, 102])

    result = array.array('B', scanline)
    pngfilters.undo_filter_paeth(3, scanline, scanprev, result)
    assert list(result) == [8, 10, 9, 108, 111, 113]  # paeth
