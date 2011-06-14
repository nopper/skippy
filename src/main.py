import cPickle as pickle
import time

from mpi4py import MPI
from stencil import Stencil
from functional import offsets

def main(matrix_file, rows=None, cols=None):
    start = time.time()
    matrix = pickle.load(open(matrix_file, "r"))
    print "%.10f seconds to load the matrix" % (time.time() - start)

    start = time.time()
    st = Stencil(offsets)
    st.apply(matrix, rows, cols)
    print "%.10f seconds to apply on %d processors" % \
            (time.time() - start, MPI.COMM_WORLD.Get_size() - 1)

def sequential(matrix_file):
    print "Trying sequential version"
    start = time.time()
    matrix = pickle.load(open(matrix_file, "r"))
    print "%.10f seconds to load the matrix" % (time.time() - start)

    st = Stencil(offsets)
    start = time.time()
    st.seq_apply(matrix)
    print "%.10f seconds to apply sequentially" % \
            (time.time() - start)
    #matrix.dump()
