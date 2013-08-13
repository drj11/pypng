import cython
from libc.stdlib cimport abs as c_abs
cimport cpython.array

@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
cpdef inline int undo_filter_sub(int filter_unit, unsigned char[::1] scanline,
                             unsigned char[::1] previous, unsigned char[::1] result)

@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
cpdef inline int do_filter_sub(int filter_unit, unsigned char[::1] scanline,
                             unsigned char[::1] previous, unsigned char[::1] result)

@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
cpdef inline int undo_filter_up(int filter_unit, unsigned char[::1] scanline,
                         unsigned char[::1] previous, unsigned char[::1] result)

@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
cpdef inline int do_filter_up(int filter_unit, unsigned char[::1] scanline,
                         unsigned char[::1] previous, unsigned char[::1] result)

@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
cpdef inline int undo_filter_average(int filter_unit, unsigned char[::1] scanline,
                              unsigned char[::1] previous, unsigned char[::1] result)

@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
cpdef inline int do_filter_average(int filter_unit, unsigned char[::1] scanline,
                              unsigned char[::1] previous, unsigned char[::1] result)

@cython.locals(pa=cython.int, pb=cython.int, pc=cython.int, p=cython.int)
cdef inline unsigned char _paeth(unsigned char a, unsigned char b, unsigned char c)


@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar)
cpdef inline int undo_filter_paeth(int filter_unit, unsigned char[::1] scanline,
                            unsigned char[::1] previous, unsigned char[::1] result)

@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar)
cpdef inline int do_filter_paeth(int filter_unit, unsigned char[::1] scanline,
                            unsigned char[::1] previous, unsigned char[::1] result)

@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int)                         
cpdef inline int convert_rgb_to_rgba(unsigned char[::1] row, unsigned char[::1] result)

@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int, lum=cython.int)
cpdef inline int convert_l_to_rgba(unsigned char[::1] row, unsigned char[::1] result)

@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int, lum=cython.int)
cpdef inline convert_la_to_rgba(unsigned char[::1] row, unsigned char[::1] result)
        