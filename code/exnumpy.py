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
    of the right shape, then populate it row-by-row from PyPNG's data.
    The numpy array mimics PyPNG's representation; it will have
    dimensions ``(row_count,column_count*plane_count)``.
'''
image_boxed_row_flat_pixels=numpy.zeros((row_count,plane_count*column_count),
                                      dtype=numpy.uint16)
for row_index, one_boxed_row_flat_pixels in enumerate(pngdata):
    image_boxed_row_flat_pixels[row_index,:]=one_boxed_row_flat_pixels

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
                  (row_count,column_count,plane_count) )


''' ============= '''

''' If you have a data array for an RGB image, as described above,
    and you want to create a png image file from it.
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
    Image_as_list_of_boxed_row_flat_pixel_lists = []
    for row in numpy.reshape(data, (-1, column_count*plane_count)):
        Image_as_list_of_boxed_row_flat_pixel_lists.append(row.tolist())
    pngWriter.write(pngfile,
                    Image_as_list_of_boxed_row_flat_pixel_lists)
finally:
    pngfile.close()

