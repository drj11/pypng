#cython: boundscheck=False
#cython: wraparound=False
class BaseFilter:
    def __init__(self, bitdepth=8, interlace=None, rows=None, prev=None):
        if bitdepth > 8:
            self.fu = bitdepth // 8
        else:
            self.fu = 1
        self.prev = bytearray() if prev is None else bytearray(prev)

    def undo_filter_sub(self, scanline, result):
        """Undo sub filter."""

        ai = 0
        # Loops starts at index fu.  Observe that the initial part
        # of the result is already filled in correctly with scanline.
        for i in range(self.fu, len(result)):
            x = scanline[i]
            a = result[ai]
            result[i] = (x + a) & 0xff
            ai += 1
        return 0

    def do_filter_sub(self, scanline, result):
        """Sub filter."""

        ai = 0
        for i in range(self.fu, len(result)):
            x = scanline[i]
            a = scanline[ai]
            result[i] = (x - a) & 0xff
            ai += 1
        return 0

    def undo_filter_up(self, scanline, result):
        """Undo up filter."""
        for i in range(len(result)):
            x = scanline[i]
            b = self.prev[i]
            result[i] = (x + b) & 0xff
        return 0

    def do_filter_up(self, scanline, result):
        """Up filter."""

        for i in range(len(result)):
            x = scanline[i]
            b = self.prev[i]
            result[i] = (x - b) & 0xff
        return 0

    def undo_filter_average(self, scanline, result):
        """Undo average filter."""

        ai = -self.fu
        for i in range(len(result)):
            x = scanline[i]
            if ai < 0:
                a = 0
            else:
                a = result[ai]
            b = self.prev[i]
            result[i] = (x + ((a + b) >> 1)) & 0xff
            ai += 1
        return 0

    def do_filter_average(self, scanline, result):
        """Average filter."""

        ai = -self.fu
        for i in range(len(result)):
            x = scanline[i]
            if ai < 0:
                a = 0
            else:
                a = scanline[ai]
            b = self.prev[i]
            result[i] = (x - ((a + b) >> 1)) & 0xff
            ai += 1
        return 0

    def _paeth(self, a, b, c):
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            return a
        elif pb <= pc:
            return b
        else:
            return c

    def undo_filter_paeth(self, scanline, result):
        """Undo Paeth filter."""

        ai = -self.fu
        for i in range(len(result)):
            x = scanline[i]
            if ai < 0:
                a = c = 0
            else:
                a = result[ai]
                c = self.prev[ai]
            b = self.prev[i]
            result[i] = (x + self._paeth(a, b, c)) & 0xff
            ai += 1
        return 0

    def do_filter_paeth(self, scanline, result):
        """Paeth filter."""

        # http://www.w3.org/TR/PNG/#9Filter-type-4-Paeth
        ai = -self.fu
        for i in range(len(result)):
            x = scanline[i]
            if ai < 0:
                a = c = 0
            else:
                a = scanline[ai]
                c = self.prev[ai]
            b = self.prev[i]
            result[i] = (x - self._paeth(a, b, c)) & 0xff
            ai += 1
        return 0

    def filter_scanline_(self, filter_type, line, result):
        """Apply a scanline filter to a scanline.
        `filter_type` specifies the filter type (0 to 4) also there are
        adaptive filters 5 (criteria is sum) and 6 (criteria is entropy);
        'line` specifies the current (unfiltered) scanline as a sequence
        of bytes;
        """

        assert 0 <= filter_type < 5
        fa = filter_type
        if not bool(self.prev):
        # We're on the first line.  Some of the filters can be reduced
        # to simpler cases which makes handling the line "off the top"
        # of the image simpler.  "up" becomes "none"; "paeth" becomes
        # "left" (non-trivial, but true). "average" needs to be handled
        # specially.
            if filter_type == 2:  # "up"
                #return line
                fa = 0
            elif filter_type == 3:
                self.prev = bytearray([0] * len(line))
            elif filter_type == 4:  # "paeth"
                fa = 1

        if fa == 1:
            self.do_filter_sub(line, result)
        elif fa == 2:
            self.do_filter_up(line, result)
        elif fa == 3:
            self.do_filter_average(line, result)
        elif fa == 4:
            self.do_filter_paeth(line, result)

        return 0

    # Todo: color conversion functions should be moved
    # to a separate part in future
    def convert_la_to_rgba(self, row, result):
        for i in range(len(row) // 3):
            for j in range(3):
                result[(4 * i) + j] = row[2 * i]
            result[(4 * i) + 3] = row[(2 * i) + 1]
        return 0

    def convert_l_to_rgba(self, row, result):
        """Convert a grayscale image to RGBA. This method assumes the alpha
        channel in result is already correctly initialized."""

        for i in range(len(row) // 3):
            for j in range(3):
                result[(4 * i) + j] = row[i]
        return 0

    def convert_rgb_to_rgba(self, row, result):
        """Convert an RGB image to RGBA. This method assumes the alpha
        channel in result is already correctly initialized."""

        for i in range(len(row) // 3):
            for j in range(3):
                result[(4 * i) + j] = row[(3 * i) + j]
        return 0

