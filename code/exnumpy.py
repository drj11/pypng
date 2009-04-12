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
pngfile= open("picture.png", 'rb')
pngReader=png.Reader(file=pngfile)
pngAsDirect=pngReader.asDirect()
row_count=pngAsDirect[1]
column_count=pngAsDirect[0]
pngdata=pngAsDirect[2]
meta=pngAsDirect[3]
bitdepth=meta['bitdepth']
plane_count=meta['planes']

# Make sure we're dealing with RGB files
assert plane_count == 3

''' Boxed row flat pixel:
      list([R,G,B, R,G,B, R,G,B],
           [R,G,B, R,G,B, R,G,B])
    Array dimensions for this example:  (2,9)

    image_boxed_row_flat_pixels
        will contain the image as a two-dimensional numpy array
        mimicking pypng's representatiom
         and has dimensions (row_count,column_count*plane_count)
'''
image_boxed_row_flat_pixels=numpy.zeros((row_count,plane_count*column_count),
                                      dtype=numpy.uint16)
row_index=0
for one_boxed_row_flat_pixels in pngdata:
  image_boxed_row_flat_pixels[row_index,:]=one_boxed_row_flat_pixels
  row_index+=1

pngAsDirect=None
pngfile.close()


''' Reconfigure for easier referencing, similar to
        Boxed row boxed pixel:
            list([ (R,G,B), (R,G,B), (R,G,B) ],
                 [ (R,G,B), (R,G,B), (R,G,B) ])
    Array dimensions for this example:  (2,3,3)

    data  will contain the image as a three-dimensional numpy array
         and have dimensions (row_count,column_count,plane_count))

'''
data = numpy.reshape(image_boxed_row_flat_pixels,
                  (row_count,column_count,plane_count) )


''' ============= '''

''' If you have a data array for an RGB image, as described above,
    and you want to create a png image file from it.
'''

row_count, column_count, plane_count = data.shape
assert plane_count==3

pngfile= open('picture_out.png', 'wb')
try:
  pngWriter = png.Writer(column_count, row_count,
                         greyscale=False,
                         alpha=False,
                         bitdepth=16)
  Image_as_list_of_boxed_row_flat_pixel_lists = []
  for row in xrange(row_count):
    Image_as_list_of_boxed_row_flat_pixel_lists.append(
                         numpy.reshape(data[row,:,:],
                                   (column_count*plane_count,)
).tolist() )
  print Image_as_list_of_boxed_row_flat_pixel_lists
  pngWriter.write(pngfile,
                  Image_as_list_of_boxed_row_flat_pixel_lists)
finally:
  pngfile.close()




