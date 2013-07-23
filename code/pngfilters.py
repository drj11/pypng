#cython: boundscheck=False
#cython: wraparound=False
'''
Created on 22.07.2013

@author: scond_000
'''


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
    return None


def undo_filter_up(filter_unit, scanline, previous, result):
    """Undo up filter."""

    for i in range(len(result)):
        x = scanline[i]
        b = previous[i]
        result[i] = (x + b) & 0xff
    return None


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
    return None


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
    return None


def convert_la_to_rgba(row, result):
    for i in range(3):
        result[i::4] = row[0::2]
    result[3::4] = row[1::2]
    return None


def convert_l_to_rgba(row, result):
    """Convert a grayscale image to RGBA. This method assumes the alpha
    channel in result is already correctly initialized."""
    for i in range(3):
        result[i::4] = row
    return None


def convert_rgb_to_rgba(row, result):
    """Convert an RGB image to RGBA. This method assumes the alpha
    channel in result is already correctly initialized."""
    for i in range(3):
        result[i::4] = row[i::3]
    return None
