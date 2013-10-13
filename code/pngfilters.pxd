import cython
from libc.stdlib cimport abs as c_abs
cimport cpython.array

ctypedef unsigned char[::1] buf_arr

cdef inline int len(buf_arr line):
	return line.shape[0]

cdef class BaseFilter:
	cdef int fu
	cdef public unsigned char[::1] prev
	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
	cdef int undo_filter_sub(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
	cdef int do_filter_sub(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
	cdef int undo_filter_up(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
	cdef int do_filter_up(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
	cdef int undo_filter_average(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
	cdef int do_filter_average(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(pa=cython.int, pb=cython.int, pc=cython.int, p=cython.int)
	cdef unsigned char _paeth(self, unsigned char a, unsigned char b, unsigned char c)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar)
	cdef int undo_filter_paeth(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar)
	cdef int do_filter_paeth(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(fa = cython.int)
	cpdef int filter_scanline(self, int filter_type, unsigned char[::1] line, unsigned char[::1] result)

	cpdef int unfilter_scanline(self, int filter_type, unsigned char[::1] line, unsigned char[::1] result)

	@cython.locals(i=cython.int, j=cython.int)
	cpdef convert_la_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)

	@cython.locals(i=cython.int, j=cython.int)
	cpdef int convert_l_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)
	
	@cython.locals(i=cython.int, j=cython.int)                         
	cpdef int convert_rgb_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)
	