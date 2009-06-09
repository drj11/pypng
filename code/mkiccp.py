#!/usr/bin/env python
# $URL$
# $Rev$
# Make ICC Profile

# References
#
# [ICC 2001] ICC Specification ICC.1:2001-04 (Profile version 2.4.0)
# [ICC 2004] ICC Specification ICC.1:2004-10 (Profile version 4.2.0.0)

import struct

# Local module.
import iccp

def encodefuns():
    """Returns a dictionary mapping ICC type signature sig to encoding
    function.  Each function returns a string comprising the content of
    the encoded value.  To form the full value, the type sig and the 4
    zero bytes should be prefixed (8 bytes).
    """

    def desc(ascii):
        """Return textDescription type [ICC 2001] 6.5.17.  The ASCII part is
        filled in with the string `ascii`, the Unicode and ScriptCode parts
        are empty."""

        ascii += '\x00'
        l = len(ascii)

        return struct.pack('>L%ds2LHB67s' % l,
                           l, ascii, 0, 0, 0, 0, '')

    def text(ascii):
        """Return textType [ICC 2001] 6.5.18."""

        return ascii + '\x00'

    def curv(f=None, n=256):
        """Return a curveType, [ICC 2001] 6.5.3.  If no arguments are
        supplied then a TRC for a linear response is generated (no entries).
        If an argument is supplied and it is a number (for *f* to be a
        number it  means that ``float(f)==f``) then a TRC for that
        gamma value is generated.
        Otherwise `f` is assumed to be a function that maps [0.0, 1.0] to
        [0.0, 1.0]; an `n` element table is generated for it.
        """

        if f is None:
            return struct.pack('>L',  0)
        try:
            if float(f) == f:
                return struct.pack('>LH', 1, int(round(f*2**8)))
        except (TypeError, ValueError):
            pass
        assert n >= 2
        table = []
        M = float(n-1)
        for i in range(n):
            x = i/M
            table.append(int(round(f(x) * 65535)))
        return struct.pack('>L%dH' % n, n, *table)

    return locals()

def encode(tsig, *l):
    """Encode a Python value as an ICC type.  `tsig` is the type
    signature to (the first 4 bytes of the encoded value, see [ICC 2004]
    section 10.
    """

    fun = encodefuns()
    if tsig not in fun:
        raise "No encoder for type %r." % tsig
    v = fun[tsig](*l)
    return tsig + '\x00'*4 + v

def black(m):
    """Return a function that maps all values from 0 to m to 0, and maps
    the range [m,1.0] into [0.0, 1.0] linearly.
    """

    m = float(m)

    def f(x):
        if x <= m:
            return 0.0
        return (x-m)/(1.0-m)
    return f

def profile(out, tags):
    """`tags` is a dictionary mapping *sig* to *value*, where *sig* is a
    4 byte signature string, and *value* is the encoded values for the
    tag element.
    """

    it = iccp.Profile().greyInput()
    it.rawtagdict = tags
    it.write(out)

# For monochrome input the required tags are (See [ICC 2001] 6.3.1.1):
# profileDescription [ICC 2001] 6.4.32
# grayTRC [ICC 2001] 6.4.19
# mediaWhitePoint [ICC 2001] 6.4.25
# copyright [ICC 2001] 6.4.13

def agreyprofile(out):
    tags = dict(cprt=encode('text', 'For the use of all mankind.'), 
      desc=encode('desc', 'an ICC profile'),
      wtpt=struct.pack('4sL12s', 'XYZ ', 0, iccp.D50()),
      kTRC=encode('curv', black(0.07)),
      )

    return profile(out, tags)

def main():
    import sys
    agreyprofile(sys.stdout)

if __name__ == '__main__':
    main()
