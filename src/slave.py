#!/usr/bin/env python
from mpi4py import MPI
from stencil import StencilWorker

def slave():
    worker = StencilWorker(*MPI.COMM_WORLD.scatter(root=0))
    worker.start()
