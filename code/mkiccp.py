#!/usr/bin/env python
# $URL$
# $Rev$
# Make ICC Profile

# References
#
# [ICC 2001] ICC Specification ICC.1:2001-04 (Profile version 2.4.0)
# [ICC 2004] ICC Specification ICC.1:2004-10 (Profile version 4.2.0.0)

import struct

def ICCdatetime(t=None):
    """`t` should be a gmtime tuple (as returned from
    ``time.gmtime()``)."""

    import time
    if t is None:
        t = time.gmtime()
    return struct.pack('>6H', *t[:6])

def s15f16(x):
    """Convert float to ICC s15Fixed16Number."""

    return int(round(x * 2**16))

def D50():
    """Return D50 illuiminant as an XYZNumber."""

    # See [ICC 2001] A.1
    return struct.pack('>3l', *map(s15f16, [0.9642, 1.0000, 0.8249]))

def header(out, size=999):
    out.write(struct.pack('>3L4s4s4s12s4s4LQL12sL',
      size,
      0,                # CMM Type signature
      0x02000000,       # Profile version
      'scnr',           # Device Class
      'GRAY',           # Color Space
      'XYZ ',           # Profile Connection Space
      ICCdatetime(),    # Profile creation time
      'acsp',           # Profile file signature
      0,                # Primary Platform signature
      # Flags should probbably by 0x00000003 for MDIS PNG files.
      0,                # Flags
      0,                # Device Manufacturer
      0,                # Device Model
      0x0000000000000008,       # Attributes
      0,                # Rendering Intent
      D50(),            # PCS Illuminant
      0)                # Creator Signature
      )
    out.write('\x00' * 44)

def profile(out, s):
    """`s` is a string comprising the entire tag section."""

    # It "just knows" that an ICC profile header is 128 bytes.
    header(out, len(s) + 128)
    out.write(s)

def tags(tag):
    """`tag` should be a dictionary of (*signature*, *element*) pairs, where
    *signature* (the key) is a length 4 string, and *element* is the content of
    the tag element (another string).  `tag` can instead, be a list of
    pairs; it is passed to the ``dict`` constructor before using.

    Returns a string.
    """

    tag = dict(tag)
    n = len(tag)
    tablelen = 12*n
    
    # Build the tag table in two parts.  A list of 12-byte tags, and a
    # string of element data.  Offset is the offset from the start of
    # the profile to the start of the element data (so the offset for
    # the next element is this offset plus the length of the element
    # string so far).
    offset = 128 + tablelen + 4
    # The table.  As a string.
    table = ''
    # The element data
    element = ''
    for k,v in tag.items():
        table += struct.pack('>4s2L', k, offset + len(element), len(v))
        element += v
    return struct.pack('>L', n) + table + element

def ICCdesc(ascii):
    """Return textDescription type [ICC 2001] 6.5.17.  The ASCII part is
    filled in with the string `ascii`, the Unicode and ScriptCode parts
    are empty."""

    ascii += '\x00'
    l = len(ascii)

    return struct.pack('>4s2L%ds2LHB67s' % l,
                       'desc', 0, l, ascii, 0, 0, 0, 0, '')

def ICCtext(ascii):
    """Return textType [ICC 2001] 6.5.18."""

    return 'text\x00\x00\x00\x00' + ascii + '\x00'

def ICCcurv(f=None, n=256):
    """Return a curveType, [ICC 2001] 6.5.3.  If no arguments are
    supplied then a TRC for a linear response is generated (no entries).
    If an argument is supplied and it is a floating point number (in
    particular, if ``float(f)==f``) then a TRC for that gamma value is
    generated.  Otherwise `f` is assumed to be a function that maps
    [0.0, 1.0] to [0.0, 1.0]; an `n` element table is generated for it.
    """
    
    if f is None:
        return struct.pack('>4s2L', 'curv', 0, 0)
    try:
        if float(f) == f:
            return struct.pack('>4s2LH', 'curv', 0, 1, int(round(f*2**8)))
    except (TypeError, ValueError):
        pass
    table = []
    M = float(n-1)
    for i in range(n):
        x = i/M
        table.append(int(round(f(x) * 65535)))
    return struct.pack('>4s2L%dH' % n, 'curv', 0, n, *table)

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

# For monochrome input the required tags are (See [ICC 2001] 6.3.1.1):
# profileDescription [ICC 2001] 6.4.32
# grayTRC [ICC 2001] 6.4.19
# mediaWhitePoint [ICC 2001] 6.4.25
# copyright [ICC 2001] 6.4.13

def agreyprofile(out):
    s = tags(dict(cprt=ICCtext('For the use of all mankind.'), 
      desc=ICCdesc('an ICC profile'),
      wtpt=struct.pack('4sL12s', 'XYZ ', 0, D50()),
      kTRC=ICCcurv(black(0.07))
      ))

    profile(out, s)

def main():
    import sys
    agreyprofile(sys.stdout)

if __name__ == '__main__':
    main()
