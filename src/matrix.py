import itertools
import logging
import numpy
import copy

logging.basicConfig()

log = logging.getLogger("matrix")
log.setLevel(logging.INFO)

class Matrix(object):
    """
    The text below is considered a test case.

    >>> m = Matrix.from_string(6, 5, "2 3 4 5 6 5 6 8 9 1 4 4 6 7 3 6 6 3 2 3 0 4 6 3 0 3 5 1 6 99")
    >>> row, col, proc = m.derive_partition([(0, 1), (0, 2)], 100)
    >>> (row, col, proc)
    (1, 2, 15)
    >>> row, col, proc = m.derive_partition([(1, 0), (3, 0)], 100)
    >>> (row, col, proc)
    (3, 1, 10)
    >>>

    Test the limit
    >>> row, col, proc = m.derive_partition([(1, 0), (3, 0)], 8)
    >>> (row, col, proc)
    (3, 2, 5)

    >>> m = Matrix.from_string(50, 40, ' '.join([i for i in map(lambda x: str(x), range(50 *40))]))
    >>> m.derive_partition([(-3, -2), (2, 2)], 10)
    (5, 40, 10)
    >>> m.derive_partition([(-1, -1), (2, 2), (0, -1)], 111)
    (5, 4, 100)
    """

    def __init__(self, rows, cols, contents=None):
        self.rows, self.cols = rows, cols

        if contents is not None:
            self.matrix = contents
        else:
            self.matrix = numpy.empty((rows, cols))

    def clone(self):
        return copy.deepcopy(self)

    def dump(self):
        print str(self.matrix)

    @staticmethod
    def from_string(rows, cols, contents):
        mtx = Matrix(rows, cols)
        elems = itertools.imap(int,
                               contents.replace("\n", " ").strip().split(" "))
        try:
            for i in range(rows):
                for j in range(cols):
                    mtx.matrix[i][j] = elems.next()
        except StopIteration:
            pass

        return mtx

    @staticmethod
    def from_list(rows, cols, contents):
        return Matrix(rows, cols, contents)

    @staticmethod
    def random(rows, cols):
        contents = numpy.random.randint(0, 9, (rows, cols))
        return Matrix(rows, cols, contents)

    def derive_partition(self, offsets, nproc):
        """
        This method should derive a proper partition scheme starting from the
        offsets you pass in input

        @param offsets model the dependencies you need in order to properly
                       evaluate your function on the matrix.
        @param nproc number of processors you have available
        @return a tuple (rows, cols, rw) that can be used to derive the correct
                partition
        """

        def get_min_step(lst, idx):
            if not lst: return 1
            return lst[0][idx]

        row_dependent = sorted([x for x in offsets if x[0] != 0],
                               key=lambda x: abs(x[0]), reverse=True)
        col_dependent = sorted([x for x in offsets if x[1] != 0],
                               key=lambda x: abs(x[1]), reverse=True)

        # Now we need to get the maximum displacement element, so we
        # sort by using abs()

        def trivial_sol(depends, is_col=0):
            aref, bref = self.cols, self.rows
            if is_col == 0: aref, bref = bref, aref

            astep = get_min_step(depends, is_col)
            num = aref / astep

            # Adaption in the other direction is not needed since we
            # start from the barely minimum

            while num > nproc:
                if astep * 2 > self.cols:
                    break

                astep *= 2
                num = int(aref / astep)

            bstep = max(int(bref / (nproc - num)), 1)
            eproc = int((aref * bref) / (bstep * astep))

            while eproc > nproc:
                bstep *= 2
                eproc = int((aref * bref) / (bstep * astep))

            return (is_col == 0) and (astep, bstep, eproc) \
                                  or (bstep, astep, eproc)


        # If we do not depend on rows in any way we can fully exploit
        # the parallelism pattern and do a partition by rows.

        if not row_dependent:
            return trivial_sol(col_dependent, 1)
        elif not col_dependent:
            return trivial_sol(row_dependent, 0)

        log.debug("Non-trivial case evaluation triggered")

        # Now for non-trivial partition we derive the biggest square
        # that our offsets can derive.

        extract = lambda l, k, rev: sorted(filter(l, offsets), reverse=rev)

        # Sort row descending
        targets = extract(lambda x: x[0] > 0,
                          lambda x: x[0], True)

        height = targets and targets[0][0] or 0

        targets = extract(lambda x: x[0] < 0,
                          lambda x: x[0], False)

        height += targets and abs(targets[0][0]) or 0

        if height > 0:
            height += 1

        # Sort row descending
        targets = extract(lambda x: x[1] > 0,
                          lambda x: x[1], True)

        width = targets and targets[0][1] or 0

        targets = extract(lambda x: x[1] < 0,
                          lambda x: x[1], False)

        width += targets and abs(targets[0][1]) or 0

        if width > 0:
            width += 1

        log.debug("Possible partition individuated %dx%d" % (height, width))

        # Now we try to figure out how many workers we can spawn

        if self.cols % width != 0:
            width = max(1, self.cols / nproc)

        if self.rows % height != 0:
            height = max(1, self.rows / nproc)

        def throttle(is_width):
            aparam, bparam = width, height
            if not is_width: aparam, bparam = bparam, aparam

            astep = aparam
            elems = self.rows * self.cols

            while (elems / (aparam * bparam)) > nproc:
                aparam += astep

                if (elems / (aparam * bparam)) < nproc:
                    break

            return aparam

        log.debug("Trying to fit %d processors" % nproc)

        if width <= height:
            width = throttle(True)
            height = throttle(False)
        else:
            height = throttle(False)
            width = throttle(True)

        log.debug("Possible partition individuated %dx%d" % (height, width))

        eproc = int((self.cols * self.rows) / (height * width))

        return (height, width, eproc)

    def partition(self, rows, cols, idx):
        col_idx = (idx * cols)
        row_idx = int(col_idx / self.cols) * rows
        col_idx %= self.cols
        return self.extract(row_idx, rows + row_idx, col_idx, cols + col_idx)

    def extract(self, row_start, row_stop, col_start, col_stop):
        return Matrix(row_stop - row_start, col_stop - col_start,
                      self.matrix[row_start:row_stop,col_start:col_stop])

    def get(self, i, j):      return self.matrix[i][j]
    def set(self, i, j, val): self.matrix[i][j] = val

if __name__ == "__main__":
    import doctest
    doctest.testmod()
