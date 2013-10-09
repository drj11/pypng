#cython: boundscheck=False
#cython: wraparound=False

_adam7 = ((0, 0, 8, 8),
          (4, 0, 8, 8),
          (0, 4, 4, 8),
          (2, 0, 4, 4),
          (0, 2, 2, 4),
          (1, 0, 2, 2),
          (0, 1, 1, 2))

class Error(Exception):
    prefix = 'Error'
    def __str__(self):
        return self.prefix + ': ' + ' '.join(self.args)

class FormatError(Error):
    """Problem with input file format.  In other words, PNG file does
    not conform to the specification in some way and is invalid.
    """

    prefix = 'FormatError'

class ChunkError(FormatError):
    prefix = 'ChunkError'


class Filter:
    def __init__(self, bitdepth=8, interlace=None, rows=None, prev=None):
        self.fu = bitdepth // 8 if bitdepth > 8 else 1
        self.interlace = interlace
        self.restarts = []
        if self.interlace:
            for _, off, _, step in _adam7:
                self.restarts.append((rows - off - 1 + step) // step)
        self.prev = bytearray() if prev is None else bytearray(prev)