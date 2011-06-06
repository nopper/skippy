import multiprocessing
from matrix import Matrix
from collections import namedtuple

RIGHT,      \
LEFT,       \
UP,         \
DOWN,       \
UP_LEFT,    \
DOWN_RIGHT, \
UP_RIGHT,   \
DOWN_LEFT = range(8)

Connections = namedtuple('Connections', 'right left up down up_left down_right up_right down_left')

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

class Communicator(object):
    def __init__(self, parent):
        self.parent = parent
        self.mapper = \
          'right left up down up_left down_right up_right down_left'.split(' ')

    def send(self, remote, direction):
        rect = self.parent.data_segments[direction]

        if not rect:
            return

        print(str(self.parent.wid) + \
              " --> send to  : %s (direction %s)" % (str(remote),
                  self.mapper[direction]))

        print("I have to send " + str(self.parent.data_segments[direction]))

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
        m.dump()

    def receive(self, remote, direction):
        print(str(self.parent.wid) + \
              " <-- recv from: %s (direction %s)" % (str(remote),
                  self.mapper[direction]))

class Skeleton(object):
    """
    This is the base class for skeleton templates
    """
    pass

class StencilWorker(object):
    _id = 0

    def __init__(self, function, offsets, data_segments, partition, pwidth, pheight):
        self.wid = StencilWorker._id
        self.function = function
        self.offsets = offsets
        self.data_segments = data_segments
        self.partition = partition

        self.col, self.row = 0, 0
        self.width, self.height = self.partition.cols, self.partition.rows
        self.pwidth, self.pheight = pwidth, pheight

        self.connections = None
        self.comm = Communicator(self)


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

        print("List of possible targets:")
        print("Left: %s Right: %s" % (target_left, target_right))
        print("Up  : %s Down : %s" % (target_up, target_down))

        print("Up-left  : %s Up-right : %s" % (target_up_left, target_up_right))
        print("Down-left  : %s Down-right : %s" % (target_down_left, target_down_right))

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
        nw = multiprocessing.cpu_count() * 2
        rows, cols, rw = matrix.derive_partition(self.offsets, nw)

        wdict = {}
        workers = []

        for i in range(rw):
            worker = StencilWorker(self.function, self.offsets,
                                   self.data_segments,
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
        old = matrix.clone()

        for i in range(matrix.rows):
            for j in range(matrix.cols):
                val = matrix.get(i, j)

                for (x, y) in self.offsets:
                    val = self.function(val,
                                        old.get((i + x) % matrix.rows,
                                                (j + y) % matrix.cols))

                matrix.set(i, j, val)
