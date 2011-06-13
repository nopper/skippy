import logging

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
        cols = self.center.cols + self.max_left + self.max_right
        rows = self.center.rows + self.max_down + self.max_up

        destination = []

        for i in range(self.max_up, self.max_up + self.center.rows):
            row = []
            for j in range(self.max_left, self.max_left + self.center.cols):
                val = self.center.get(i - self.max_up, j - self.max_left)

                for (x, y) in offsets:
                    ioff = (i + x) % rows
                    joff = (j + y) % cols

                    if ioff < self.max_up:
                        if joff < self.max_left:
                            # UP LEFT
                            p = self.pieces[UP_LEFT]

                            try:
                                coff = self.max_left - p.cols
                                roff = self.max_up - p.rows

                                ret = p.get(ioff - roff, joff - coff)
                            except:
                                ret = 0

                        elif joff >= self.max_left + self.center.cols:
                            # UP RIGHT
                            p = self.pieces[UP_RIGHT]

                            try:
                                coff = self.center.cols + self.max_left
                                roff = self.max_up - p.rows

                                ret = p.get(ioff - roff, joff - coff)
                            except:
                                ret = 0

                        else:
                            # UP
                            p = self.pieces[UP]

                            try:
                                coff = self.max_left
                                roff = self.max_up - p.rows

                                ret = p.get(ioff - roff, joff - coff)
                            except:
                                ret = 0

                    elif ioff >= self.max_up + self.center.rows:
                        if joff < self.max_left:
                            # DOWN LEFT
                            p = self.pieces[DOWN_LEFT]

                            try:
                                coff = self.max_left - p.cols
                                roff = self.max_up + self.center.rows

                                ret = p.get(ioff - roff, joff - coff)
                            except:
                                ret = 0

                        elif joff >= self.max_left + self.center.cols:
                            # DOWN RIGHT
                            p = self.pieces[DOWN_RIGHT]

                            try:
                                coff = self.center.cols + self.max_left
                                roff = self.max_up + self.center.rows

                                ret = p.get(ioff - roff, joff - coff)
                            except:
                                ret = 0
                        else:
                            # DOWN
                            p = self.pieces[DOWN]

                            try:
                                coff = self.max_left
                                roff = self.max_up + self.center.rows

                                ret = p.get(ioff - roff, joff - coff)
                            except:
                                ret = 0
                    else:
                        if joff < self.max_left:
                            # LEFT
                            p = self.pieces[LEFT]

                            try:
                                coff = self.max_left - p.cols
                                roff = self.max_up

                                ret = p.get(ioff - roff, joff - coff)
                            except:
                                ret = 0
                        elif joff >= self.max_left + self.center.cols:
                            # RIGHT
                            p = self.pieces[RIGHT]

                            try:
                                coff = self.center.cols + self.max_left
                                roff = self.max_up

                                ret = p.get(ioff - roff, joff - coff)
                            except:
                                ret = 0
                        else:
                            ret = self.center.get(
                                ioff - self.max_up,
                                joff - self.max_left
                            )

                    val = function(val, ret)
                row.append(val)
            destination.append(row)

        return Matrix.from_list(self.center.rows, self.center.cols,
                                destination)
