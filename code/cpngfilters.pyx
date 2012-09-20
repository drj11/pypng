cimport cpython.array

#cython: boundscheck=False
#cython: wraparound=False

def undo_filter_sub(int filter_unit, unsigned char[:] scanline,
                    unsigned char[:] previous, unsigned char[:] result):
    """Undo sub filter."""

    cdef int l = len(result)
    cdef int ai = 0
    cdef unsigned char x, a

    # Loops starts at index fu.  Observe that the initial part
    # of the result is already filled in correctly with
    # scanline.
    for i in range(filter_unit, l):
        x = scanline[i]
        a = result[ai]
        result[i] = (x + a) & 0xff
        ai += 1


def undo_filter_paeth(int filter_unit, unsigned char[:] scanline,
                      unsigned char[:] previous, unsigned char[:] result):
    """Undo Paeth filter."""

    # Also used for ci.
    cdef int ai = -filter_unit
    cdef int l = len(result)
    cdef int i, pa, pb, pc, p
    cdef unsigned char x, a, b, c, pr

    for i in range(l):
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


def convert_rgb_to_rgba(unsigned char[:] row, unsigned char[:] result):
    cdef int i, l, j, k
    l = min(len(row) / 3, len(result) / 4)
    for i in range(l):
        j = i * 3
        k = i * 4
        result[k] = row[j]
        result[k + 1] = row[j + 1]
        result[k + 2] = row[j + 2]


def convert_l_to_rgba(unsigned char[:] row, unsigned char[:] result):
    cdef int i, l, j, k, lum
    l = min(len(row), len(result) / 4)
    for i in range(l):
        j = i
        k = i * 4
        lum = row[j]
        result[k] = lum
        result[k + 1] = lum
        result[k + 2] = lum


def convert_la_to_rgba(unsigned char[:] row, unsigned char[:] result):
    cdef int i, l, j, k, lum
    l = min(len(row) / 2, len(result) / 4)
    for i in range(l):
        j = i * 2
        k = i * 4
        lum = row[j]
        result[k] = lum
        result[k + 1] = lum
        result[k + 2] = lum
        result[k + 3] = row[j + 1]
