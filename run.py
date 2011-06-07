from mpi4py import MPI
from matrix import Matrix
from stencil import Stencil

from main import main
from slave import slave

rank = MPI.COMM_WORLD.Get_rank()

def run():
    if rank == 0:
        main()
    else:
        slave()

if __name__ == "__main__":
    run()
