import time
import logging

from numpy import zeros, vstack, hstack
from matrix import Matrix
from communicator.enum import UP, DOWN, LEFT, RIGHT, \
                              DOWN_LEFT, DOWN_RIGHT, \
                              UP_LEFT, UP_RIGHT

logging.basicConfig()

log = logging.getLogger("puzzle")
log.setLevel(logging.INFO)

class Puzzle(object):
    def __init__(self, center):
        self.center = center
        self.pieces = [None, ] * 8

        self.max_up    = 0
        self.max_down  = 0
        self.max_left  = 0
        self.max_right = 0

    def add_piece(self, piece, position):
        if position in (UP, UP_LEFT, UP_RIGHT):
            self.max_up = max(self.max_up, piece.rows)
        if position in (DOWN, DOWN_LEFT, DOWN_RIGHT):
            self.max_down = max(self.max_down, piece.rows)
        if position in (LEFT, DOWN_LEFT, UP_LEFT):
            self.max_left = max(self.max_left, piece.cols)
        if position in (RIGHT, DOWN_RIGHT, UP_RIGHT):
            self.max_right = max(self.max_right, piece.cols)

        self.pieces[position] = piece

    def pad(self, part, where, dtype):
        if part is None:
            if where == RIGHT and self.max_right > 0:
                return zeros((1, self.max_right))
            if where == LEFT  and self.max_left > 0:
                return zeros((1, self.max_left))
            if where == UP    and self.max_up > 0:
                return zeros((self.max_up, 1))
            if where == DOWN  and self.max_down > 0:
                return zeros((self.max_down, 1))

            return None

        if isinstance(part, Matrix): m = part.matrix
        else:                        m = part

        if where == RIGHT and m.shape[1] < self.max_right:
            pad = zeros((m.shape[0], self.max_right - m.shape[1]), dtype)
            return hstack((m, pad))

        elif where == LEFT and m.shape[1] < self.max_left:
            pad = zeros((m.shape[0], self.max_left - m.shape[1]), dtype)
            return hstack((pad, m))

        elif where == UP and m.shape[0] < self.max_up:
            pad = zeros((self.max_up - m.shape[0], m.shape[1]), dtype)
            return vstack((pad, m))

        elif where == DOWN and m.shape[0] < self.max_down:
            pad = zeros((self.max_down - m.shape[0], m.shape[1]), dtype)
            return vstack((m, pad))

        return m

    def apply(self, offsets, function):
        start = time.time()
        matrix = self.center.matrix.copy()

        up = self.pad(self.pieces[UP], UP, matrix.dtype)
        down = self.pad(self.pieces[DOWN], DOWN, matrix.dtype)

        is_empty = lambda x: x is not None

        matrix = vstack(filter(is_empty, (up, matrix, down)))

        left  = self.pad(self.pieces[LEFT], LEFT, matrix.dtype)
        right = self.pad(self.pieces[RIGHT], RIGHT, matrix.dtype)

        upl   = self.pad(self.pad(self.pieces[UP_LEFT], UP, matrix.dtype),
                         LEFT, matrix.dtype)
        downl = self.pad(self.pad(self.pieces[DOWN_LEFT], DOWN, matrix.dtype),
                         LEFT, matrix.dtype)
        upr   = self.pad(self.pad(self.pieces[UP_RIGHT], UP, matrix.dtype),
                         RIGHT, matrix.dtype)
        downr = self.pad(self.pad(self.pieces[DOWN_RIGHT], DOWN, matrix.dtype),
                         RIGHT, matrix.dtype)

        # Hacky fix
        if self.max_up == 0:    upl, upr     = None, None
        if self.max_down == 0:  downl, downr = None, None
        if self.max_left == 0:  downl, upl   = None, None
        if self.max_right == 0: downr, upr   = None, None

        coll = filter(is_empty, (upl, left, downl))

        if coll: left = vstack(coll)
        else:    left = None

        coll = filter(is_empty, (upr, right, downr))

        if coll: right = vstack(coll)
        else:    right = None

        matrix = hstack(filter(is_empty, (left, matrix, right)))

        log.info("%.10f seconds to create auxiliary matrix" % \
                 (time.time() - start))

        dest = self.center
        rows, cols = matrix.shape
        idisp, jdisp = self.max_up, self.max_left

        for i in range(self.max_up, self.max_up + self.center.rows):
            for j in range(self.max_left, self.max_left + self.center.cols):
                val = matrix[i][j]

                for (x, y) in offsets:
                    val = function(val, matrix[(i + x) % rows][(j + y) % cols])

                dest.matrix[i - idisp][j - jdisp] = val
