$URL$
$Rev$


README for PyPNG
drj@pobox.com

PyPNG provides Python code for encoding/decoding PNG files.  In
particular png.py is a Python module written entirely in Python.


INSTALLATION

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
see the example in the man/ex/ directory.


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
