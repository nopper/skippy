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

    def apply(self):
        cols = self.center.cols + self.max_left + self.max_right
        rows = self.center.rows + self.max_down + self.max_up

        log.info("Creating a temporary matrix of %d rows and %d cols" % (rows,
            cols))

        m = []

        for row in range(rows):
            lst = []
            for col in range(cols):
                lst.append(0)
            m.append(lst)

        p = self.pieces[UP_LEFT]

        if p:
            row_start = self.max_up - p.rows
            col_start = self.max_left - p.cols

            for i in range(p.rows):
                for j in range(p.cols):
                    m[row_start + i][col_start + j] = p.get(i, j)

        p = self.pieces[UP]

        if p:
            row_start = self.max_up - p.rows
            col_start = self.max_left

            for i in range(p.rows):
                for j in range(p.cols):
                    m[row_start + i][col_start + j] = p.get(i, j)

        p = self.pieces[UP_RIGHT]

        if p:
            row_start = self.max_up - p.rows
            col_start = self.max_left + self.center.cols

            for i in range(p.rows):
                for j in range(p.cols):
                    m[row_start + i][col_start + j] = p.get(i, j)

        p = self.pieces[LEFT]

        if p:
            row_start = self.max_up
            col_start = self.max_left - p.cols

            for i in range(p.rows):
                for j in range(p.cols):
                    m[row_start + i][col_start + j] = p.get(i, j)

        p = self.pieces[RIGHT]

        if p:
            row_start = self.max_up
            col_start = self.max_left + self.center.cols + (self.max_right - p.cols)

            for i in range(p.rows):
                for j in range(p.cols):
                    m[row_start + i][col_start + j] = p.get(i, j)

        p = self.pieces[DOWN_LEFT]

        if p:
            row_start = self.max_up + self.center.rows
            col_start = self.max_left - p.cols

            for i in range(p.rows):
                for j in range(p.cols):
                    m[row_start + i][col_start + j] = p.get(i, j)

        p = self.pieces[DOWN]

        if p:
            row_start = self.max_up + self.center.rows
            col_start = self.max_left

            for i in range(p.rows):
                for j in range(p.cols):
                    m[row_start + i][col_start + j] = p.get(i, j)

        p = self.pieces[DOWN_RIGHT]

        if p:
            row_start = self.max_up + self.center.rows
            col_start = self.max_left + self.center.cols

            for i in range(p.rows):
                for j in range(p.cols):
                    m[row_start + i][col_start + j] = p.get(i, j)

        # Let's put our center contents
        row_start = self.max_up
        col_start = self.max_left
        p = self.center

        for i in range(p.rows):
            for j in range(p.cols):
                m[row_start + i][col_start + j] = p.get(i, j)

        return Matrix.from_list(rows, cols, m)
