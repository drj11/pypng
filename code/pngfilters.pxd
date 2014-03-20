import cython
from libc.stdlib cimport abs as c_abs
cimport cpython.array
from cython.view cimport array as carray

ctypedef unsigned char[::1] buf_arr

cdef inline int len_ba(buf_arr line):
	return line.shape[0]
	
cdef inline buf_arr newarray(int length):
	cdef buf_arr res
	cdef int i
	#Seek for more effective view init (but without bytearrays)
	res = carray(shape=(length,), itemsize=sizeof(uchar), format="B")
	for i in range(length):
		res[i] = 0
	return res

cdef class BaseFilter:
	cdef int fu
	cdef public unsigned char[::1] prev
	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
	cpdef _undo_filter_sub(self, buf_arr scanline, buf_arr previous, buf_arr result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar)
	cdef void __do_filter_sub(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
	cpdef _undo_filter_up(self, buf_arr scanline, buf_arr previous, buf_arr result)

	@cython.locals(i=cython.int, x=cython.uchar, b=cython.uchar)
	cdef void __do_filter_up(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
	cpdef _undo_filter_average(self, buf_arr scanline, buf_arr previous, buf_arr result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar)                         
	cdef void __do_filter_average(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(pa=cython.int, pb=cython.int, pc=cython.int, p=cython.int)
	cdef unsigned char __paeth(self, unsigned char a, unsigned char b, unsigned char c)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar, pa=cython.uchar, pb=cython.uchar, pc=cython.uchar, pr=cython.uchar, p=cython.uchar)
	cpdef _undo_filter_paeth(self, buf_arr scanline, buf_arr previous, buf_arr result)

	@cython.locals(ai = cython.int, i=cython.int, x=cython.uchar, a=cython.uchar, b=cython.uchar, c=cython.uchar)
	cdef void __do_filter_paeth(self, unsigned char[::1] scanline, unsigned char[::1] result)

	@cython.locals(fa = cython.int)
	cpdef filter_scanline(self, int filter_type, unsigned char[::1] line, unsigned char[::1] result)

	@cython.locals(i=cython.int, j=cython.int)
	cpdef convert_la_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)

	@cython.locals(i=cython.int, j=cython.int)
	cpdef convert_l_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)
	
	@cython.locals(i=cython.int, j=cython.int)                         
	cpdef convert_rgb_to_rgba(self, unsigned char[::1] row, unsigned char[::1] result)
	