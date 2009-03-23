$URL$
$Rev$


README for PyPNG
drj@pobox.com

PyPNG provides Python code for encoding/decoding PNG files.  In
particular png.py is a Python module written entirely in Python.


INSTALLATION

PyPNG requires Python version 2.3 (and that's all), or any compatible
higher version.

PyPNG comes with a setup.py script to use with distutils.  After
unpacking the distribution, cd into the directory and execute the
command:

python setup.py install

The png module will be installed; "import png" will allow you to use it
from your Python programs.

Alternatively, you can copy code/png.py wherever you like.  It's intended
that you can copy png.py into your application and distribute it.


GETTING STARTED

"import png" then "help(png)" should be a good place to start.  Also,
lickable HTML documentation appears in the html/ directory.  If HTML is
no good then you could try the ReST sources in the man/ directory.


RELEASE NOTES

(For issues see http://code.google.com/p/pypng/issues/list )

Release 0.0.3 (This release)

The following issues have been fixed:

  Issue 14:  Does not read PAM files.
  Issue 15:  Does not write PAM files.
  Issue 25:  Incorrect handling of tRNS chunk.
  Issue 26:  asRGBA8 method crashes out for color type 2 images.
  Issue 27:  Fails on Python 2.3.

Release 0.0.2

The following issues have been fixed:

  Issue 8:  Documentation is not lickable.
  Issue 9:  Advantage over PIL is not clear.
  Issue 19: Bogus message for PNM inputs with unsupported maxval
  Issue 20: Cannot write large PNG files

Release 0.0.1

Stuff happened.


MANIFEST

.../ - top-level crud (like this README, and setup.py).
.../code/ - the Python code.
.../html/ - lickable manuals (generated).
.../man/ - manuals (in source/plain-text).


PROJECT HOME

Currently hosted on Google Code: http://code.google.com/p/pypng/

Come join the love.  And submit bug reports and things.


REFERENCES

Python: www.python.org
PNG: http://www.w3.org/TR/PNG/
