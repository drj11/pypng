.. $URL$
.. $Rev$

Why Use PyPNG?
==============

- PyPNG is pure Python;
- install with pip: ``pip install pypng``;
- install traditional way: ``python setup.py install``;
- install by copying ``code/png.py``;
- read/write all PNG bitdepths (16 bit!) and colour modes;
- read/write interlace PNG;
- convert to/from 1-, 2-, 3-, 4- channel NetPBM PAM files;
- support for ``sBIT`` chunk;
- support for many other PNG chunk types;
- fun command line utilities.

Conversion to and from PAM files means that on the command line,
processing PAM files can be mixed with processing PNG files.

Because PyPNG is dedicated to PNG files it often supports more
formats and features of PNG file than general purpose libraries.
