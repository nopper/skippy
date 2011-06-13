import logging
import numpy

from matrix import Matrix
from communicator.enum import *

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

    def apply(self, offsets, function):
        def get(position, i, j):
            p = self.pieces[position]

            if p is None:
                return 0

            if position == UP_LEFT:
                coff = self.max_left - p.cols
                roff = self.max_up - p.rows
            elif position == UP_RIGHT:
                coff = self.center.cols + self.max_left
                roff = self.max_up - p.rows
            elif position == UP:
                coff = self.max_left
                roff = self.max_up - p.rows
            elif position == DOWN_LEFT:
                coff = self.max_left - p.cols
                roff = self.max_up + self.center.rows
            elif position == DOWN_RIGHT:
                coff = self.center.cols + self.max_left
                roff = self.max_up + self.center.rows
            elif position == DOWN:
                coff = self.max_left
                roff = self.max_up + self.center.rows
            elif position == LEFT:
                coff = self.max_left - p.cols
                roff = self.max_up
            elif position == RIGHT:
                coff = self.center.cols + self.max_left
                roff = self.max_up

            i -= roff
            j -= coff

            if i < 0 or i > p.cols or j < 0 or j > p.rows:
                return 0
            else:
                return p.get(i, j)

        cols = self.center.cols + self.max_left + self.max_right
        rows = self.center.rows + self.max_down + self.max_up

        destination = numpy.empty((self.center.rows, self.center.cols))

        for i in range(self.max_up, self.max_up + self.center.rows):
            row = []
            for j in range(self.max_left, self.max_left + self.center.cols):
                val = self.center.get(i - self.max_up, j - self.max_left)

                for (x, y) in offsets:
                    ioff = (i + x) % rows
                    joff = (j + y) % cols

                    if ioff < self.max_up:
                        if joff < self.max_left:
                            ret = get(UP_LEFT, ioff, joff)
                        elif joff >= self.max_left + self.center.cols:
                            ret = get(UP_RIGHT, ioff, joff)
                        else:
                            ret = get(UP, ioff, joff)

                    elif ioff >= self.max_up + self.center.rows:
                        if joff < self.max_left:
                            ret = get(DOWN_LEFT, ioff, joff)
                        elif joff >= self.max_left + self.center.cols:
                            ret = get(DOWN_RIGHT, ioff, joff)
                        else:
                            ret = get(DOWN, ioff, joff)
                    else:
                        if joff < self.max_left:
                            ret = get(LEFT, ioff, joff)
                        elif joff >= self.max_left + self.center.cols:
                            ret = get(RIGHT, ioff, joff)
                        else:
                            ret = self.center.get(
                                ioff - self.max_up,
                                joff - self.max_left
                            )

                    val = function(val, ret)
                destination[i - self.max_up][j - self.max_left] = val

        return Matrix.from_list(self.center.rows, self.center.cols,
                                destination)
