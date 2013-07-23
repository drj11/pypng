import cython
from libc.stdlib cimport abs as c_abs
cimport cpython.array

@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
cpdef inline int undo_filter_sub(int filter_unit, unsigned char[:] scanline,
                             unsigned char[:] previous, unsigned char[:] result)

@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
cpdef inline int undo_filter_up(int filter_unit, unsigned char[:] scanline,
                         unsigned char[:] previous, unsigned char[:] result)

@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
cpdef inline int undo_filter_average(int filter_unit, unsigned char[:] scanline,
                              unsigned char[:] previous, unsigned char[:] result)

@cython.locals(ai = cython.int, i=cython.int, pa=cython.int, pb=cython.int, pc=cython.int, p=cython.int,
                 x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar, pr=cython.uchar)
cpdef inline int undo_filter_paeth(int filter_unit, unsigned char[:] scanline,
                            unsigned char[:] previous, unsigned char[:] result)

@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int)                         
cpdef inline int convert_rgb_to_rgba(unsigned char[:] row, unsigned char[:] result)

@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int, lum=cython.int)
cpdef inline int convert_l_to_rgba(unsigned char[:] row, unsigned char[:] result)

@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int, lum=cython.int)
cpdef inline convert_la_to_rgba(unsigned char[:] row, unsigned char[:] result)
        