import logging
from mpi4py import MPI
from enum import REVERSED, LABELS

logging.basicConfig()

log = logging.getLogger("comm-mpi")
log.setLevel(logging.INFO)

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
            row_stop = rect[0]
            row_start = 0
        elif rect[0] < 0:
            row_stop = self.parent.height
            row_start = self.parent.height - abs(rect[0])
        else:
            row_stop = self.parent.height
            row_start = 0

        if rect[1] > 0:
            col_stop = rect[1]
            col_start = 0
        elif rect[1] < 0:
            col_stop = self.parent.width
            col_start = self.parent.width - abs(rect[1])
        else:
            col_stop = self.parent.width
            col_start = 0

        m = self.parent.partition.extract(row_start, row_stop, \
                                          col_start, col_stop)

        log.debug("%d --> send to  : %s (direction %s)" % \
                  (rank - 1, str(remote), LABELS[direction]))

        comm.send(m, dest=remote + 1, tag=direction)
        log.debug("%d --> send to  : %s DONE" % (rank - 1, str(remote)))

    def receive(self, remote, direction):
        rect = self.parent.data_segments[REVERSED[direction]]

        if rect is None or remote is None or remote == rank - 1:
            return

        log.debug("%d <-- recv from: %s (direction %s)" % \
                  (rank - 1, str(remote), LABELS[direction]))

        data = comm.recv(source=remote + 1, tag=REVERSED[direction])

        log.debug("%d <-- recv from: %s (direction %s) DONE" % \
                  (rank - 1, str(remote), LABELS[direction]))

        return data
