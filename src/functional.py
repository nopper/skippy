import numpy

offsets = ((-1, 0), (0, -1), (0, 1), (1, 0))

def variance(a, b):
    if isinstance(a, int):
        n, mean, m2 = 0, 0, 0
    elif isinstance(a, list):
        n, mean, m2 = a

    n += 1
    delta = b - mean
    mean += delta / n
    m2 = m2 + delta * (b - mean)

    if n == 4:
        return m2/(n - 1)
    else:
        return [n, mean, m2]

function = variance

def linsolve(a, b):
    """
    Here we try to interpret the matrix as follows
      2
    1 5 3
      4

    5 will be our a parameter. The aim of the function is to find a solution to
    the given algebrical system:
     1x + 3y = 5
     2x + 4y = 5

    Then the mean value is calculated and putted in the center.
    """
    if isinstance(a, int):
        return [a, b]
    elif isinstance(a, list):
        a.append(b)

        if len(a) == 5:
            equations = numpy.array(((a[1], a[4]),
                                     (a[2], a[3])))
            given     = numpy.array((a[0], a[0]))
            try:
                return numpy.linalg.solve(equations, given).mean()
            except Exception:
                return 0
        return a


#offsets = ((-2, -1), (-2, 0), (-2, -2))
function = min
