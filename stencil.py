import multiprocessing
from collections import namedtuple

Connections = namedtuple('Connections', 'right left up down up_left down_right up_right down_light')

class Connections(object):
    def __init__(self, right, left, up, down):
        self.right = right
        self.left = left
        self.up = up
        self.down = down

        self.up_left = None
        self.up_right = None
        self.down_left = None
        self.down_right = None

    def __repr__(self):
        return "right=%s, left=%s, up=%s, down=%s, ul=%s, ur=%s, dl=%s, dr=%s" % \
            (self.right, self.left, self.up, self.down,
             self.up_left, self.up_right, self.down_left, self.down_right)

class Skeleton(object):
    """
    This is the base class for skeleton templates
    """
    pass

class StencilWorker(object):
    _id = 0

    def __init__(self, function, partition, pwidth, pheight):
        self.wid = StencilWorker._id
        self.function = function
        self.partition = partition

        self.col, self.row = 0, 0
        self.width, self.height = self.partition.cols, self.partition.rows
        self.pwidth, self.pheight = pwidth, pheight

        self.connections = None


        print("Worker %d has %s" % (StencilWorker._id, self.partition))
        StencilWorker._id += 1

    def autoconnect(self, wdict, rows=None, cols=None):
        if self.connections:
            self.connections.up_left = self.connections.up.connections.left
            self.connections.up_right = self.connections.up.connections.right
            self.connections.down_left = self.connections.down.connections.left
            self.connections.down_right = self.connections.down.connections.right

            print(str(self) + " " + str(self.connections))
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

    def start(self):
        pr = lambda x: print(str(self.wid) + str(x))

        if self.col + self.width == self.pwidth:
            pr("invio destra a " + str(self.connections.right))

        if self.row + self.height == self.pheight:
            pr("invio giu a " + str(self.connections.down))

        if self.col > 0:
            pr("invio sinistra a " + str(self.connections.left))
            if self.row > 0:
                pr("invio sopra a " + str(self.connections.up))

        pr("ricevo sinistra da " + str(self.connections.left))
        pr("ricevo sopra da " + str(self.connections.up))
        pr("ricevo destra da " + str(self.connections.right))
        pr("ricevo giu da " + str(self.connections.down))

        if self.col + self.width < self.pwidth:
            pr("invia destra a " + str(self.connections.right))

        if self.row + self.height < self.pheight:
            pr("invia giu a " + str(self.connections.down))

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

    def apply(self, matrix):
        nw = multiprocessing.cpu_count() * 2
        rows, cols, rw = matrix.derive_partition(self.offsets, nw)

        wdict = {}
        workers = []

        for i in range(rw):
            worker = StencilWorker(self.function,
                                   matrix.partition(rows, cols, i),
                                   matrix.cols, matrix.rows)
            wdict[worker.wid] = worker
            workers.append(worker)

        print(matrix.rows/rows)
        print(matrix.cols/cols)

        for worker in workers:
            worker.autoconnect(wdict, matrix.rows / rows, matrix.cols / cols)

        for worker in workers:
            worker.autoconnect(wdict)

        for worker in workers:
            worker.start()


    def seq_apply(self, matrix):
        for i in range(matrix.rows):
            for j in range(matrix.cols):
                val = matrix.get(i, j)

                for (x, y) in self.offsets:
                    val = self.function(val,
                                        matrix.get((i + x) % matrix.rows,
                                                   (j + y) % matrix.cols))

                matrix.set(i, j, val)
