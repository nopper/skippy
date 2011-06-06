"""
This file is just a test file. We start with a simple matrix
and then we apply the minimum over the all structure.
"""

from matrix import Matrix
from stencil import Stencil

def main():
    m = Matrix.from_string(6, 6, """
2 3 4 5 6 4
5 6 8 9 1 2
4 4 6 7 3 4
6 6 3 2 3 6
0 4 6 3 0 7
3 5 1 6 99 1""")

    #st = Stencil(min, ((-1,0), (0,-1), (0,1), (1,0)))

    st = Stencil(min, ((-2, -1), (-2, 0), (-2, -3)))
    print("Before running:")
    m.dump()

    st.seq_apply(m)
    print("After running:")
    m.dump()

    print("Applying in parallel:")
    #st.apply(m)

if __name__ == "__main__":
    main()
