import logging

from mpi4py import MPI

from enum import *
from matrix import Matrix

logging.basicConfig()

log = logging.getLogger("comm-mpi")
log.setLevel(logging.DEBUG)

comm = MPI.COMM_WORLD

class Communicator(object):
    def __init__(self, parent):
        self.parent = parent
        self.mapper = \
          'right left up down up_left down_right up_right down_left'.split(' ')

        self.create_sockets()

    def create_sockets(self):
        self.reverse_map = [
            LEFT, RIGHT, DOWN, UP, DOWN_RIGHT, UP_LEFT, DOWN_LEFT, UP_RIGHT
        ]

        self.sockets = [None,] * 8

        for dir, port in zip(self.parent.data_segments, range(8)):
            if not dir: continue

    def send(self, remote, direction):
        rect = self.parent.data_segments[direction]

        if not rect:
            return

        log.debug(str(self.parent.wid) + \
              " --> send to  : %s (direction %s)" % (str(remote),
                  self.mapper[direction]))

        log.debug("I have to send " + str(self.parent.data_segments[direction]))

        if rect[0] > 0:
            row_stop = self.parent.height
            row_start = self.parent.height - rect[0]
        elif rect[0] < 0:
            row_stop = abs(rect[0])
            row_start = 0
        else:
            row_stop = self.parent.height
            row_start = 0

        if rect[1] > 0:
            col_stop = self.parent.width
            col_start = self.parent.width - rect[1]
        elif rect[1] < 0:
            col_stop = abs(rect[1])
            col_start = 0
        else:
            col_stop = self.parent.width
            col_start = 0

        out = []

        for i in range(row_start, row_stop, 1):
            col = []
            for j in range(col_start, col_stop, 1):
                col.append(self.parent.partition.get(i, j))
            out.append(col)

        m = Matrix.from_list(row_stop - row_start, col_stop - col_start, out)
        comm.send(m, dest=remote + 1)

    def receive(self, remote, direction):
        if remote is None:
            return

        log.debug(str(self.parent.wid) + \
              " <-- recv from: %s (direction %s)" % (str(remote),
                  self.mapper[direction]))

        return comm.recv(source=remote + 1)
