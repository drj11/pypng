#!/usr/bin/env python
# $URL$
# $Rev$

# Numpy example.
# Original code created by Mel Raab, modified by David Jones.

'''
  RGB PNG FILES, pypng and numpy
  (abstracted from functioning code)
'''

import png
import numpy


''' If you have a png file for an RGB image,
    and want to create a numpy array of data from it.
'''
# Read the file "picture.png" from the current directory.  The `Reader`
# class can take a filename, a file-like object, or the byte data
# directly; this suggests alternatives such as using urllib to read
# an image from the internet:
# png.Reader(file=urllib.urlopen('http://www.libpng.org/pub/png/PngSuite/basn2c16.png'))
pngReader=png.Reader(filename='picture.png')
pngAsDirect=pngReader.asDirect()
# Tuple unpacking, using multiple assignment, is very useful for the
# result of asDirect (and other methods).
# See
# http://docs.python.org/tutorial/introduction.html#first-steps-towards-programming
row_count, column_count, pngdata, meta = pngAsDirect
bitdepth=meta['bitdepth']
plane_count=meta['planes']

# Make sure we're dealing with RGB files
assert plane_count == 3

''' Boxed row flat pixel:
      list([R,G,B, R,G,B, R,G,B],
           [R,G,B, R,G,B, R,G,B])
    Array dimensions for this example:  (2,9)

    Create `image_boxed_row_flat_pixels` as a two-dimensional numpy
    array of the right shape, then populate it row-by-row from PyPNG's data.
    The numpy array mimics PyPNG's representation; it will have
    dimensions ``(row_count,column_count*plane_count)``.
'''
image_boxed_row_flat_pixels=numpy.zeros((row_count,plane_count*column_count),
                                      dtype=numpy.uint16)
for row_index, one_boxed_row_flat_pixels in enumerate(pngdata):
    image_boxed_row_flat_pixels[row_index,:]=one_boxed_row_flat_pixels
# An alternative to the above is to use ``numpy.vstack``.  This is very
# simple and direct:
#   numpy.vstack(pngdata)
# When used like this, numpy will pick the resulting array's data type;
# in practice it seems to pick ``numpy.int32``, which is large enough to
# hold any pixel value for any PNG image but uses 4 bytes per value when
# 1 or 2 would be enough.  If you want to choose the result array's data
# type, you can convert each row to a numpy array of the chosen type.
# Here we use the fact that any numpy basic type can be used as a function
# to convert an ordinary Python sequence to a numpy array.  See
# http://docs.scipy.org/doc/numpy/user/basics.types.html for more
# details.
#   numpy.vstack(itertools.imap(numpy.uint16, pngdata))
# Do not be tempted to use ``numpy.asarray``; when passed an iterator
# (`pngdata` is often an iterator) it will attempt to create a size 1
# array with the iterator as its only element.

del pngAsDirect
del pngReader
del pngdata


''' Reconfigure for easier referencing, similar to
        Boxed row boxed pixel:
            list([ (R,G,B), (R,G,B), (R,G,B) ],
                 [ (R,G,B), (R,G,B), (R,G,B) ])
    Array dimensions for this example:  (2,3,3)

    ``data`` will contain the image as a three-dimensional numpy array
         and have dimensions ``(row_count,column_count,plane_count)``.
'''
data = numpy.reshape(image_boxed_row_flat_pixels,
                     (row_count,column_count,plane_count))


''' ============= '''

''' Convert numpy data array to PNG image file.

    If the data is three-dimensional, as it is above, the best thing
    to do is reshape it into a two-dimensional array with a shape of
    ``(row_count, column_count*plane_count)``.  Because a
    two-dimensional numpy array is an iterator, it can be passed
    directly to the ``png.Writer.write`` method.
'''

row_count, column_count, plane_count = data.shape
assert plane_count==3

pngfile = open('picture_out.png', 'wb')
try:
    # This example assumes that you have 16-bit pixel values in the data
    # array (that's what the ``bitdepth=16`` argument is for).
    # If you don't, then the resulting PNG file will likely be
    # very dark.  Hey, it's only an example.
    pngWriter = png.Writer(column_count, row_count,
                           greyscale=False,
                           alpha=False,
                           bitdepth=16)
    # As of 2009-04-13 passing a numpy array that has an element type
    # that is a numpy integer type (for example, the `data` array has an
    # element type of ``numpy.uint16``) generates a deprecation warning.
    # This is probably a bug in numpy; it may go away in the future.
    # The code still works despite the warning.
    # See http://code.google.com/p/pypng/issues/detail?id=44
    pngWriter.write(pngfile,
                    numpy.reshape(data, (-1, column_count*plane_count)))
finally:
    pngfile.close()

