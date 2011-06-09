import sys
from mpi4py import MPI
from main import main, sequential
from slave import slave

def run(matrix_file, rows=None, cols=None):
    rank = MPI.COMM_WORLD.Get_rank()

    if rank == 0:
        main(matrix_file, rows, cols)
    else:
        slave()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s <par|seq> <matrix-file> [rowsxcols]" % sys.argv[0]
        sys.exit(0)

    if sys.argv[1] == 'seq':
        sequential(sys.argv[2])
    elif sys.argv[1] == 'par':
        if len(sys.argv) == 4:
            params = map(lambda x: int(x), sys.argv[3].split('x'))
        else:
            params = (None, None)

        run(sys.argv[2], *params)
