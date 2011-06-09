try:
    import cPickle as pickle
except ImportError:
    import pickle

import time

from matrix import Matrix
from stencil import Stencil
from functional import function

offsets = ((-1,0), (0,-1), (0,1), (1,0))
#offsets = ((-2, -1), (-2, 0), (-2, -2))

def main(matrix_file, rows=None, cols=None):
    start = time.time()
    matrix = pickle.load(open(matrix_file, "r"))
    print "%.2f seconds to load the matrix" % (time.time() - start)

    st = Stencil(function, offsets)
    st.apply(matrix, rows, cols)

def sequential(matrix_file):
    print "Trying sequential version"
    matrix = pickle.load(open(matrix_file, "r"))

    st = Stencil(function, offsets)
    st.seq_apply(matrix)
    matrix.dump()
