#!/usr/bin/env python

from mpi4py import MPI
from stencil import StencilWorker
from functional import function

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def slave():
    worker = StencilWorker(*comm.recv(source=0, tag=0))
    worker.start()
