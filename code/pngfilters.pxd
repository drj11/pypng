import cython
from libc.stdlib cimport abs as c_abs
cimport cpython.array

cdef class Filter:
	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
	cdef inline int undo_filter_sub(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
	cdef inline int do_filter_sub(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
	cdef inline int undo_filter_up(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
	cdef inline int do_filter_up(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
	cdef inline int undo_filter_average(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
	cdef inline int do_filter_average(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(pa=cython.int, pb=cython.int, pc=cython.int, p=cython.int)
	cdef inline unsigned char _paeth(self, unsigned char a, unsigned char b, unsigned char c)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar)
	cdef inline int undo_filter_paeth(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar)
	cdef inline int do_filter_paeth(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(f = cython.ccall)
	cdef inline int filter_scanline(self, unsigned char filter_type, unsigned char[::1] line)

	@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int)                         
	cdef inline int convert_rgb_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)

	@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int, lum=cython.int)
	cdef inline int convert_l_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)

	@cython.locals(i=cython.int, l=cython.int, j=cython.int, k=cython.int, lum=cython.int)
	cdef inline convert_la_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)
        