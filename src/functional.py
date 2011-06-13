import math

offsets = ((-1,0), (0,-1), (0,1), (1,0))

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

#offsets = ((-2, -1), (-2, 0), (-2, -2))
function = min
