import logging

from mpi4py import MPI

from enum import *
from matrix import Matrix

logging.basicConfig()

log = logging.getLogger("comm-mpi")
log.setLevel(logging.DEBUG)

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

class Communicator(object):
    def __init__(self, parent):
        self.parent = parent

    def send(self, remote, direction):
        rect = self.parent.data_segments[direction]

        if rect is None or remote == None or remote == rank - 1:
            return

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

        log.debug("%d --> send to  : %s (direction %s)" % (rank - 1, str(remote),
                  LABELS[direction]))

        comm.send(m, dest=remote + 1, tag=direction)
        log.debug("%d --> send to  : %s DONE" % (rank - 1, str(remote)))

    def receive(self, remote, direction):
        rect = self.parent.data_segments[direction]

        if rect is None or remote is None or remote == rank - 1:
            return

        log.debug("%d <-- recv from: %s (direction %s)" % (rank - 1, str(remote),
                  LABELS[REVERSED[direction]]))

        return comm.recv(source=remote + 1, tag=direction)
