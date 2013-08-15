#cython: boundscheck=False
#cython: wraparound=False
'''
Created on 22.07.2013

@author: scond_000
'''
# NOTE: Remove binary (pyd/so) version and pngfilters.c if you change this file
# Rebuild them with Cython if you can


def undo_filter_sub(filter_unit, scanline, previous, result):
    """Undo sub filter."""
    ai = 0
    # Loops starts at index fu.  Observe that the initial part
    # of the result is already filled in correctly with scanline.
    for i in range(filter_unit, len(result)):
        x = scanline[i]
        a = result[ai]
        result[i] = (x + a) & 0xff
        ai += 1
    return 0


def do_filter_sub(filter_unit, scanline, previous, result):
    """Sub filter."""
    ai = 0
    for i in range(filter_unit, len(result)):
        x = scanline[i]
        a = scanline[ai]
        result[i] = (x - a) & 0xff
        ai += 1
    return 0


def undo_filter_up(filter_unit, scanline, previous, result):
    """Undo up filter."""
    for i in range(len(result)):
        x = scanline[i]
        b = previous[i]
        result[i] = (x + b) & 0xff
    return 0


def do_filter_up(filter_unit, scanline, previous, result):
    """Up filter."""
    for i in range(len(result)):
        x = scanline[i]
        b = previous[i]
        result[i] = (x - b) & 0xff
    return 0


def undo_filter_average(filter_unit, scanline, previous, result):
    """Undo average filter."""
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
    return 0


def do_filter_average(filter_unit, scanline, previous, result):
    """Average filter."""
    ai = -filter_unit
    for i in range(len(result)):
        x = scanline[i]
        if ai < 0:
            a = 0
        else:
            a = scanline[ai]
        b = previous[i]
        result[i] = (x - ((a + b) >> 1)) & 0xff
        ai += 1
    return 0


def _paeth(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c


def undo_filter_paeth(filter_unit, scanline, previous, result):
    """Undo Paeth filter."""
    ai = -filter_unit
    for i in range(len(result)):
        x = scanline[i]
        if ai < 0:
            a = c = 0
        else:
            a = result[ai]
            c = previous[ai]
        b = previous[i]
        result[i] = (x + _paeth(a, b, c)) & 0xff
        ai += 1
    return 0


def do_filter_paeth(filter_unit, scanline, previous, result):
    """Paeth filter."""
    # http://www.w3.org/TR/PNG/#9Filter-type-4-Paeth
    ai = -filter_unit
    for i in range(len(result)):
        x = scanline[i]
        if ai < 0:
            a = c = 0
        else:
            a = scanline[ai]
            c = previous[ai]
        b = previous[i]
        result[i] = (x - _paeth(a, b, c)) & 0xff
        ai += 1
    return 0


def convert_la_to_rgba(row, result):
    for i in range(3):
        result[i::4] = row[0::2]
    result[3::4] = row[1::2]
    return 0


def convert_l_to_rgba(row, result):
    """Convert a grayscale image to RGBA. This method assumes the alpha
    channel in result is already correctly initialized."""
    for i in range(3):
        result[i::4] = row
    return 0


def convert_rgb_to_rgba(row, result):
    """Convert an RGB image to RGBA. This method assumes the alpha
    channel in result is already correctly initialized."""
    for i in range(3):
        result[i::4] = row[i::3]
    return 0
