try:
    import cPickle as pickle
except ImportError:
    import pickle

import time

from matrix import Matrix
from stencil import Stencil
from functional import function, offsets

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
