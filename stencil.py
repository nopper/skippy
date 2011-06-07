import sys
import logging
import multiprocessing

from mpi4py import MPI

from matrix import Matrix
from communicator.enum import *
from communicator.mpi import Communicator

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
name = MPI.Get_processor_name()

logging.basicConfig()

log = logging.getLogger("stencil")
log.setLevel(logging.INFO)

class Skeleton(object):
    """
    This is the base class for skeleton templates
    """
    pass

class StencilWorker(object):
    _id = 0

    def __init__(self, offsets, data_segments, partition, pwidth, pheight, \
                 connections=None):
        self.wid = StencilWorker._id
        self.offsets = offsets
        self.data_segments = data_segments
        self.partition = partition

        self.col, self.row = 0, 0
        self.width, self.height = self.partition.cols, self.partition.rows
        self.pwidth, self.pheight = pwidth, pheight

        self.connections = connections

        if rank == 0:
            log.debug("Worker %d has %s" % (StencilWorker._id, self.partition))
            StencilWorker._id += 1
        else:
            self.comm = Communicator(self)

    def autoconnect(self, wdict, rows=None, cols=None):
        if self.connections:
            self.connections.up_left = self.connections.up.connections.left
            self.connections.up_right = self.connections.up.connections.right
            self.connections.down_left = self.connections.down.connections.left
            self.connections.down_right = self.connections.down.connections.right

            log.debug(str(self) + " " + str(self.connections))
            log.debug("Converting connection to id pairs for %d" % self.wid)

            # Now let's convert it back to id pairs
            for lbl in 'right left up down up_left down_right up_right down_left'.split(' '):
                obj = getattr(self.connections, lbl)
                if not isinstance(obj, int):
                    setattr(self.connections, lbl,  obj.wid)

            return

        tot = int(rows * cols)

        i_col = self.wid % cols
        i_row = int(self.wid / rows)

        start = cols * i_row

        # Here we calculate our position in the general matrix
        self.col, self.row = i_col * self.height, i_row * self.width

        self.connections = Connections(
            wdict[(self.wid + 1) % cols + start],
            wdict[(self.wid - 1) % cols + start],
            wdict[(self.wid - rows) % tot],
            wdict[(self.wid + rows) % tot],
        )

    def __repr__(self):
        return 'Worker(%d [%d %d %d %d])' % (self.wid, self.row, self.col,
                self.width, self.height)

    def bootstrap(self):
        log.info("Sending partition to worker %d" % self.wid)

        data = (self.offsets, self.data_segments, self.partition, \
                self.pwidth, self.pheight, self.connections)

        comm.send(data, dest=self.wid + 1, tag=0)

    def start(self):
        log.info("Worker started on processor %d %s" % (rank, name))

        if self.col + self.width == self.pwidth:
            self.comm.send(self.connections.right, RIGHT)

        if self.row + self.height == self.pheight:
            self.comm.send(self.connections.down_right, DOWN_RIGHT)
            self.comm.send(self.connections.down,       DOWN)
            self.comm.send(self.connections.down_left,  DOWN_LEFT)

        if self.col > 0:
            if self.row > 0:
                self.comm.send(self.connections.up_left, UP_LEFT)
                self.comm.send(self.connections.up,      UP)

            self.comm.send(self.connections.left, LEFT)

        if self.row > 0:
            self.comm.send(self.connections.up_right, UP_RIGHT)

        self.comm.receive(self.connections.left,       LEFT)
        self.comm.receive(self.connections.up_left,    UP_LEFT)
        self.comm.receive(self.connections.up,         UP)
        self.comm.receive(self.connections.up_right,   UP_RIGHT)
        self.comm.receive(self.connections.right,      RIGHT)
        self.comm.receive(self.connections.down_right, DOWN_RIGHT)
        self.comm.receive(self.connections.down,       DOWN)
        self.comm.receive(self.connections.down_left,  DOWN_LEFT)

        if self.col + self.width < self.pwidth:
            self.comm.send(self.connections.right, RIGHT)

        if self.row + self.height < self.pheight:
            # Riordinate giusto per performance
            self.comm.send(self.connections.down_left,  DOWN_LEFT)
            self.comm.send(self.connections.down,       DOWN)
            self.comm.send(self.connections.down_right, DOWN_RIGHT)


#        for i in range(self.partition.rows):
#            for j in range(self.partition.cols):
#                val = self.partition.get(i, j)
#
#                for (x, y) in self.offsets:
#                    val = self.function(val,
#                                        self.partition.get((i + x) % self.partition.rows,
#                                                   (j + y) % self.partition.cols))
#
#                self.partition.set(i, j, val)

class Stencil(object):
    def __init__(self, function, offsets):
        self.function = function
        self.offsets = offsets
        self.analyze_offsets()

    def analyze_offsets(self):
        """
        This function is in charge of extracting the proper sub-partitions that
        must be transmitted to the other workers in a stencil fashion
        """
        extract = lambda l, rev: sorted(filter(l, self.offsets), reverse=rev)

        right = extract(lambda x: x[0] == 0 and x[1] > 0, True)
        left  = extract(lambda x: x[0] == 0 and x[1] < 0, False)
        up    = extract(lambda x: x[0] < 0 and x[1] == 0, False)
        down  = extract(lambda x: x[0] > 0 and x[1] == 0, True)

        # Sort the first key which is the row so order is False since we are
        # interested in far jumps which are < 0
        up_left  = extract(lambda x: x[0] < 0 and x[1] < 0, False)

        if up_left:
            max_row = up_left[0][0]
            max_col = sorted(up_left, key=lambda x: x[1], reverse=False)[0][1]
            target_up_left = (max_row, max_col)
        else:
            target_up_left = None

        up_right = extract(lambda x: x[0] < 0 and x[1] > 0, False)

        if up_right:
            max_row = up_right[0][0]
            max_col = sorted(up_right, key=lambda x: x[1], reverse=True)[0][1]
            target_up_right = (max_row, max_col)
        else:
            target_up_right = None

        # Sort the first key which is the row so order is True since we are
        # interested in far jumps which are > 0
        down_left = extract(lambda x: x[0] > 0 and x[1] < 0, True)

        if down_left:
            max_row = down_left[0][0]
            max_col = sorted(down_left, key=lambda x: x[1], reverse=False)[0][1]
            target_down_left = (max_row, max_col)
        else:
            target_down_left = None

        down_right = extract(lambda x: x[0] > 0 and x[1] > 0, True)

        if down_right:
            max_row = down_left[0][0]
            max_col = sorted(down_left, key=lambda x: x[1], reverse=True)[0][1]
            target_down_right = (max_row, max_col)
        else:
            target_down_right = None

        target_right = right and right[0] or None
        target_left  = left and left[0] or None
        target_up    = up and up[0] or None
        target_down  = down and down[0] or None

        log.debug("List of possible targets:")
        log.debug("Left: %s Right: %s" % (target_left, target_right))
        log.debug("Up  : %s Down : %s" % (target_up, target_down))

        log.debug("Up-left  : %s Up-right : %s" % (target_up_left, target_up_right))
        log.debug("Down-left  : %s Down-right : %s" % (target_down_left, target_down_right))

        # Now we try to assign correct mapping. Please beware that if you
        # change the enumeration order you also need to change the order of
        # this assignment.
        self.data_segments = [
            target_right,
            target_left,
            target_up,
            target_down,
            target_up_left,
            target_down_right,
            target_up_right,
            target_down_left
        ]

    def apply(self, matrix):
        nw = comm.Get_size()
        rows, cols, rw = matrix.derive_partition(self.offsets, nw)

        wdict = {}
        workers = []

        for i in range(rw):
            worker = StencilWorker(self.offsets,
                                   self.data_segments,
                                   matrix.partition(rows, cols, i),
                                   matrix.cols, matrix.rows)
            wdict[worker.wid] = worker
            workers.append(worker)

        log.debug(matrix.rows/rows)
        log.debug(matrix.cols/cols)

        for worker in workers:
            worker.autoconnect(wdict, matrix.rows / rows, matrix.cols / cols)

        for worker in workers:
            worker.autoconnect(wdict)

        for worker in workers:
            worker.bootstrap()
            #worker.start()


    def seq_apply(self, matrix):
        old = matrix.clone()

        for i in range(matrix.rows):
            for j in range(matrix.cols):
                val = matrix.get(i, j)

                for (x, y) in self.offsets:
                    val = self.function(val,
                                        old.get((i + x) % matrix.rows,
                                                (j + y) % matrix.cols))

                matrix.set(i, j, val)
