
def window(rows, info, tl, br):
    """*rows* and *info* are the rows and info object for
    a PNG image as might be returned by png.asDirect().
    A new *rows* and *info* are returned that represent
    a windowed image.
    The window is an axis aligned rectangle with opposite corners
    at *tl* and *br* (each being an (x,y) pair).

    As in ImageMagick (0,0) is the top-left.

    Coordinates are usually integers, but can be passed as
    `None` in which case the relevant image boundary will be
    used (0 for left, image width for right, 0 for top, image
    height for bottom).
    """

    width, height = info["size"]

    left, top = tl
    right, bottom = br

    if top is None:
        top = 0
    if left is None:
        left = 0
    if bottom is None:
        bottom = height
    if right is None:
        right = width

    if not (0 <= left < right <= width):
        raise NotImplementedError()
    if not (0 <= top < bottom <= height):
        raise NotImplementedError()
    # Compute left and right index bounds for each row,
    # given that each row is a flat row of values.
    l = left * info["planes"]
    r = right * info["planes"]

    def itercrop():
        """An iterator to perform the crop."""

        for i, row in enumerate(rows):
            if i < top:
                continue
            if i >= bottom:
                # Same as "raise StopIteration"
                return
            yield row[l:r]

    info = dict(info, size=(right - left, bottom - top))
    return itercrop(), info

