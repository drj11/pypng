#!/usr/bin/env python

"""
Example code integrating RGB PNG files, PyPNG and NumPy
(abstracted from Mel Raab's functioning code)
"""

import numpy

import png
import pngsuite


"""
Reading from PNG file into numpy array.

If you have a PNG file for an RGB image,
and want to create a numpy array of data from it.
"""
# Here we take the bytes from an entry in the pngsuite module.
# That's so we can execute this example as a test and we don't
# need a file in the filesystem.
# If you do need a file you can use
# png.Reader(filename="picture.png")
# instead.
pngReader = png.Reader(bytes=pngsuite.basn2c16)

# Tuple unpacking, using multiple assignment, is
# very useful for the result of asDirect (and other methods).
row_count, column_count, pngdata, meta = pngReader.asDirect()
bitdepth = meta["bitdepth"]
plane_count = meta["planes"]

# Make sure we're dealing with RGB files
assert plane_count == 3

""" Boxed row flat pixel:
      list([R,G,B, R,G,B, R,G,B],
           [R,G,B, R,G,B, R,G,B])
    Array dimensions for this example:  (2,9)

    Create `image_2d` as a two-dimensional NumPy array by
    stacking a sequence of 1-dimensional arrays (rows).
    The NumPy array is a sequence of rows, which is ideal for PyPNG;
    it will have dimensions ``(row_count,column_count*plane_count)``.
"""
# The use of ``numpy.uint16``, below,
# converts each row to a NumPy array with data type ``numpy.uint16``.
# This is a feature of NumPy,
# discussed further in http://docs.scipy.org/doc/numpy/user/basics.types.html .
# You can use avoid the explicit conversion with ``numpy.vstack(pngdata)``,
# but then NumPy will pick the array's data type;
# in practice it seems to pick ``numpy.int32``,
# which is large enough to hold any pixel value for any PNG image but
# uses 4 bytes per value when 1 or 2 would be enough.
# --- extract 001 start
image_2d = numpy.vstack(map(numpy.uint16, pngdata))
# --- extract 001 end

del pngReader
del pngdata


""" Reconfigure for easier referencing, similar to:
            list([ (R,G,B), (R,G,B), (R,G,B) ],
                 [ (R,G,B), (R,G,B), (R,G,B) ])
    Array dimensions for this example:  (2,3,3)

    ``image_3d`` will contain the image as a three-dimensional numpy
    array, having dimensions ``(row_count,column_count,plane_count)``.
"""
# --- extract 002 start
image_3d = numpy.reshape(image_2d, (row_count, column_count, plane_count))
# --- extract 002 end


""" ============= """

""" Convert NumPy image_3d array to PNG image file.

    If the data is three-dimensional, as it is above,
    the best thing to do is reshape it into a two-dimensional array with
    a shape of ``(row_count, column_count*plane_count)``.
    Because a two-dimensional numpy array is an iterator, it
    can be passed directly to the ``png.Writer.write`` method.
"""

row_count, column_count, plane_count = image_3d.shape
assert plane_count == 3

with open("picture_out.png", "wb") as out:
    # This example assumes that you have 16-bit pixel values in the data
    # array (that's what the ``bitdepth=16`` argument is for).
    # If you don't, then the resulting PNG file will likely be very dark.
    pngWriter = png.Writer(
        column_count, row_count, greyscale=False, alpha=False, bitdepth=16
    )
    # --- extract 003 start
    image_2d = numpy.reshape(image_3d, (-1, column_count * plane_count))
    pngWriter.write(out, image_2d)
# --- extract 003 end
