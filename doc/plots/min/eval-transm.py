import sys
import numpy

results = []
for line in sys.stdin.readlines():
    dim, time = line.strip().split(':')
    results.append(float(time) / (int(dim) ** 2))

print numpy.array(results).mean()
