# Vision for PyPNG 0.1

# Design principles

A single object will represent image, including source and
destination files (if applicable), metadata, streaming
state, and conversions. This object will also be iterable.
Object will also "know" its preferred iterator item (rows,
pixels, boxed rows, etc).

Arguments via info dict / namespace.

generally monad/jQuery style:

    rows = png.load("foo.png").asL()
    for row in rows:
       blah blah blah

or

    numpy.vstack(png.load("foo.png").convertGrey())

metadata available in .info() method:

    rows.info()


Writing similarly:

    png.from_iter([[0, 1, 2], [1, 2, 3]], "L;2").save("out.png")

(`from_iter` same as current `from_array`)

Object obtained from `png.load()` or `png.from_iter()` is in
principle same type. (so, can convert bit-depth on writing as
well as reading).

In principle format neutral when reading/writing, but in
practice will only support PNG and PNM.

Convert via info.
One cute thing is that instead of having lots of `.asRGB` and
`.asRGBA8` methods, could have a single `.as(info)` method
that _receives_ an `info` object and coerces the stream as
specified.

So, `.as(dict(greyscale=False))` would ensure RGB or RGBA;
`.as(dict(bitdepth=8))` would scale up to 8-bit.

# Convention

`as` methods generally do not change (perceptual) value. For
example, a greyscale image can always be represented in an
(equal bitdepth) RGB format by replicating the intensities.

`as` methods will abort (raise Exception) if format cannot be
changed without changing value.

`convert` methods are at liberty to change values to
approximately equivalent ones.

# Q

How to deal with random PNG chunks?

# Unified mode

Each element of the axes list corresponds to an axis of the array.
The type of the axis is denoted by a short string
(at the moment, a single character string).

x - X axis
y - Y axis
c - channel (0, 1, 2, 3, for R, G, B, A)

    axes = ['y', 'x', 'c']      # aka "boxed"
    shape = [300, 400, 3]

    axes = ['y', 'x|c']         # aka "packed"
    shape = [300, 400, 3]

When an axis specification is of the form "P|Q" then this
indicates 2 axes ravelled onto one; the ravelled axis is indexed
by a single index that scans across a conceptual rectangle
formed of P and Q with Q varyng fastest. `i = k*p + q` where `k`
is the size of the Q axis.

How are the factors of the channel axis denoted?

    channels = ['R', 'G', 'B', 'A']

Should that denote the bit depth too?

    channels = ['R5', 'G6', 'B5']

Can we denote floating point depths too?

    channels = ['Rf32', 'Gf32', 'Bf32']

or

    channels = ['R1.0', ...] # ?

palleted:

    channels = ['P8']

It would be nice to be able to represent a whole pixel with a
single value. Pedantically `axes = ['y', 'x', 'c']` does this,
but the "value" is a 3-element tuple (for RGB images). 

    axes = ['y', 'x']
    shape = [300, 400]
    values = 'RGBA'

`values` describes the elements of the R dimensional array.
It is either:
'i' for integer intensities (from 0 to 2**k-1;
k being the channel depth);
'RGBA' for an integer (>=0) that consists of the channel values packed,
bitwise, into a single integer.
The integer is considered as a string of bits,
left-to-right corresponding to most-to-least significant.
The rightmost channel in the value string corresponds to the least
(rightmost, in the usual way of writing integers in binary notation)
significant bits of the integer.

With pixels packed into a single integer it is less convenient
to extract channels, but it will be easier to do operations that
only consider whole pixels (for example, cropping).

# Memory in Python

[[[R, G, B, A], ...], ...]      # axes = ['y', 'x', 'c']

disaster. 5 objects per pixel.

[R, G, B, A, R, G, B, A, ...]

nice. 0 objects per pixel (unless 16-bit, see below).

[RGBA, RGBA, ...]       # values = 'RGBA'

poor. 1 object per pixel.

[R16, G16, B16, A16, ...]

disaster, 4 objects per pixel. Consider RGBA instead!
