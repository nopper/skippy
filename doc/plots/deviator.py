import sys
import re
import numpy

re_num = re.compile(".*-np\s(\d{1,2}).*")
re_comp = re.compile(".*(\d\.\d{10}) seconds to compute.*")

f = open(sys.argv[1], "r")
text = f.read()
f.close()

runs = text.split('\n\n')
d = {}

for run in runs:
  m = re_num.match(run)

  if m:
    np = m.groups(1)[0]
    times = []

    for line in run.splitlines():
      time = re_comp.findall(line)

      if time:
        times.append(float(time[0]))

    d[int(np) - 1] = numpy.array(times).std()

for (k,v) in sorted(d.items()):
  print k, v

print numpy.array([v for (k,v) in d.items()]).mean()
