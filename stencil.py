import sys
import logging

from mpi4py import MPI

from matrix import Matrix
from puzzle import Puzzle
from functional import function

from communicator.enum import *
from communicator.mpi import Communicator

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
name = MPI.Get_processor_name()

logging.basicConfig()

log = logging.getLogger("stencil")
log.setLevel(logging.INFO)

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

        self.conns = connections

        if rank == 0:
            log.debug("Worker %d has %s" % (StencilWorker._id, self.partition))
            StencilWorker._id += 1
        else:
            self.comm = Communicator(self)

    def autoconnect(self, wdict, rows=None, cols=None):
        if self.conns:
            if self.conns.up:
                self.conns.up_left = self.conns.up.conns.left
                self.conns.up_right = self.conns.up.conns.right
            if self.conns.down:
                self.conns.down_left = self.conns.down.conns.left
                self.conns.down_right = self.conns.down.conns.right

            return

        tot = int(rows * cols)

        i_col = self.wid % cols
        i_row = int(self.wid / cols)

        start = cols * i_row

        # Here we calculate our position in the general matrix
        self.col, self.row = i_col * self.height, i_row * self.width

        links = []

        for id in ((self.wid + 1) % cols + start,
                   (self.wid - 1) % cols + start,
                   (self.wid - cols) % tot,
                   (self.wid + cols) % tot):

            if id == self.wid:
                links.append(None)
            else:
                links.append(wdict[id])

        self.conns = Connections(*links)

    def __repr__(self):
        return 'Worker(%d [%d %d %d %d])' % (self.wid, self.row, self.col,
                self.width, self.height)

    def bootstrap(self, partition):
        log.info("Sending partition to worker %d" % self.wid)

        data = (self.offsets, self.data_segments, partition, \
                self.pwidth, self.pheight, self.conns)

        comm.send(data, dest=self.wid + 1, tag=0)

    def start(self):
        log.info("Worker started on processor %d %s" % (rank, name))

        # First we send all the required partitions to the neighbors and then
        # receive all the segments and reconstruct a local matrix where the
        # function will be evaluated.

        puzzle = Puzzle(self.partition)

        for lbl, enum in zip(LABELS, ORDERED):
            self.comm.send(getattr(self.conns, lbl), enum)

        for lbl, enum in zip(RLABELS, REVERSED):
            m = self.comm.receive(getattr(self.conns, lbl), enum)
            if m: puzzle.add_piece(m, enum)

        log.info("Computing...")

        matrix = puzzle.apply()

        for i in range(puzzle.max_up, puzzle.max_up + self.partition.rows):
            for j in range(puzzle.max_left, puzzle.max_left + self.partition.cols):
                val = matrix.get(i, j)

                for (x, y) in self.offsets:
                    val = function(val, matrix.get(
                        (i + x) % matrix.rows,
                        (j + y) % matrix.cols
                    ))

                self.partition.set(i - puzzle.max_up, j - puzzle.max_left, val)

        log.info("Sending back the computed sub-partition from %d" % rank)
        comm.ssend(self.partition, dest=0, tag=666)
        comm.Barrier()

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
            tgt_up_left = (max_row, max_col)
        else:
            tgt_up_left = None

        up_right = extract(lambda x: x[0] < 0 and x[1] > 0, False)

        if up_right:
            max_row = up_right[0][0]
            max_col = sorted(up_right, key=lambda x: x[1], reverse=True)[0][1]
            tgt_up_right = (max_row, max_col)
        else:
            tgt_up_right = None

        # Sort the first key which is the row so order is True since we are
        # interested in far jumps which are > 0
        down_left = extract(lambda x: x[0] > 0 and x[1] < 0, True)

        if down_left:
            max_row = down_left[0][0]
            max_col = sorted(down_left, key=lambda x: x[1], reverse=False)[0][1]
            tgt_down_left = (max_row, max_col)
        else:
            tgt_down_left = None

        down_right = extract(lambda x: x[0] > 0 and x[1] > 0, True)

        if down_right:
            max_row = down_left[0][0]
            max_col = sorted(down_left, key=lambda x: x[1], reverse=True)[0][1]
            tgt_down_right = (max_row, max_col)
        else:
            tgt_down_right = None

        tgt_right = right and right[0] or None
        tgt_left  = left and left[0] or None
        tgt_up    = up and up[0] or None
        tgt_down  = down and down[0] or None

        log.debug("List of possible targets:")
        log.debug("Left: %s Right: %s" % (tgt_left, tgt_right))
        log.debug("Up  : %s Down : %s" % (tgt_up, tgt_down))

        log.debug("Up-left  : %s Up-right : %s" % (tgt_up_left, tgt_up_right))
        log.debug("Down-left  : %s Down-right : %s" % (tgt_down_left, tgt_down_right))

        # Now we try to assign correct mapping. Please beware that if you
        # change the enumeration order you also need to change the order of
        # this assignment.

        self.data_segments = [
            tgt_left,
            tgt_right,
            tgt_down,
            tgt_up,
            tgt_down_right,
            tgt_up_left,
            tgt_down_left,
            tgt_up_right,
        ]

    def fix_data_deps(self, prow, pcol):
        """
        Try to fix data dependences to avoid bogus data
        @param prow is the number of rows each worker has assigned to
        @param pcol is the number of cols each worker has assigned to
        """
        def adjust(corner1, corner2, direction, check_idx, set_idx):
            targets = filter(lambda x: x,
                    [self.data_segments[REVERSED[corner1]],
                     self.data_segments[REVERSED[corner2]]])

            if not targets: return

            targets.sort(reverse=True, key=lambda x: abs(x[check_idx]))
            rect = targets[0]
            checker = (prow, pcol)

            # If our partition to transmit is smaller than the partition size
            # assigned it means that we are loosing part of the block needed to
            # the computation.
            if rect and abs(rect[check_idx]) < checker[check_idx]:
                target = self.data_segments[REVERSED[direction]]

                # If it is so we have to evaluate the maximum number of items
                # we have other dimension.
                if (target and abs(target[set_idx]) < abs(rect[set_idx])) or not target:

                    if check_idx == 0: out = (0, rect[set_idx])
                    else:              out = (rect[set_idx], 0)

                    self.data_segments[REVERSED[direction]] = out
                    log.info("Fixing data dependences by adding %s in %s " \
                             "direction" % (str(out), LABELS[direction]))

        adjust(UP_LEFT, DOWN_LEFT, LEFT, 0, 1)
        adjust(UP_RIGHT, DOWN_RIGHT, RIGHT, 0, 1)

        adjust(UP_LEFT, UP_RIGHT, UP, 1, 0)
        adjust(DOWN_LEFT, DOWN_RIGHT, DOWN, 1, 0)

    def apply(self, matrix, rows=None, cols=None):
        nw = comm.Get_size() - 1

        if rows is not None and cols is not None:
            log.info("Skipping auto-derivation")
            rw = (matrix.cols / cols) * (matrix.rows / rows)
        else:
            rows, cols, rw = matrix.derive_partition(self.offsets, nw)

        self.fix_data_deps(rows, cols)

        wdict = {}
        workers = []

        for i in range(rw):
            # Just assign an empty invalid partition the correct partition will
            # be derived when needed.
            worker = StencilWorker(self.offsets,
                                   self.data_segments,
                                   Matrix.from_list(rows, cols, None),
                                   matrix.cols, matrix.rows)
            wdict[worker.wid] = worker
            workers.append(worker)

        log.info("After partition => Rows: %d Cols: %d" % \
                 (matrix.rows/rows, matrix.cols/cols))

        for worker in workers:
            worker.autoconnect(wdict, matrix.rows / rows, matrix.cols / cols)
        for worker in workers:
            worker.autoconnect(wdict)
        for worker in workers:
            worker.conns.convert_to_id()
        for worker in workers:
            worker.bootstrap(matrix.partition(rows, cols, worker.wid))

        row, col = 0, 0

        for idx in range(rw):
            log.info("Reading sub-partition from client %d" % idx)
            partition = comm.recv(source=idx + 1, tag=666)

            for i in range(rows):
                for j in range(cols):
                    row_start = row * partition.rows
                    col_start = col * partition.cols

                    matrix.set(row_start + i,
                               col_start + j, partition.get(i, j))

            col += 1

            if col == matrix.cols/cols:
                col = 0
                row += 1

        log.info("Terminated.")
        comm.Barrier()

        #print "Result is"
        #matrix.dump()

    def seq_apply(self, matrix):
        old = matrix.clone()

        for i in range(matrix.rows):
            for j in range(matrix.cols):
                val = old.get(i, j)

                for (x, y) in self.offsets:
                    val = self.function(val,
                                        old.get((i + x) % matrix.rows,
                                                (j + y) % matrix.cols))

                matrix.set(i, j, val)
