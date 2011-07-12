import math

# Extracted with cat stats-4000 | grep "to apply on" | awk -F' ' '{print $1 ":" $6}'
stats_3000 = """
1:768.5506930351
2:389.0696969032
3:261.2670691013
4:197.9516479969
5:166.3430581093
6:139.4931449890
8:105.2403669357
10:84.8252170086
12:72.6171600819
15:58.2625229359
16:57.1286311150
"""

stats_4000 = """
1:1386.0492398739
2:704.1511330605
4:355.4894700050
5:286.6042079926
8:190.3507759571
10:154.2290370464
16:99.0791161060
"""

stats_5000 = """
"""

stats_6000 = """
"""

gstat = {
    3000 : stats_3000,
    4000 : stats_4000,
    5000 : stats_5000,
    6000 : stats_6000
}

class Plotter(object):
    def __init__(self, m, tseq):
        global gstat

        self.tsetup = 0
        self.transm = 3.81e-07 # assumo 10mbit
        #self.transm =2.2310691090449627e-07
        self.transm = 3.43711684842e-07
        self.noff = 2
        self.m = float(m)
        self.stats = {}
        for k, v in [x.split(':') for x in gstat[m].strip().splitlines()]:
            self.stats[int(k)] = float(v)

        self.tf = tseq / (m ** 2)

    def g(self, n):
        return (self.m ** 2) / n

    def part(self, n):
        return math.sqrt(self.g(n))

    def comm(self, l):
        return l * self.transm

    def scatter(self, n):
        return (n * self.tsetup) + n * (self.g(n) * self.transm)

    def t(self, n):
        return (2 * self.scatter(n)) + \
               (self.noff * self.comm(self.part(n))) + \
               (self.g(n) * self.tf)

    def t_id(self, n):
        return ((self.m **2) * self.tf) / n

    def run(self):
        f = open("collate-%d" % self.m, "w+")
        print >>f, "# Statistics for %dx%d" % (self.m, self.m)
        print >>f, "# <node-degree> <tc-ideal> <tc-cost-model> <tc-collected>"\
                   " <efficiency-cm> <efficiency-collected> <speedup-cm> "\
                   "<speedup-collected> <scal-cm> <scal-coll>"            \
                   " <bw-ideal> <bw-cost-model> <bw-collected>"

        for i in range(1, 17):
            tcid = self.t_id(i)
            tc   = self.t(i)

            eff = tcid / tc
            speedcm = eff * i
            scalcm = self.t(1) / self.t(i)

            out = "%d %.10f %.10f " % (i, tcid, tc)

            try:
                tccol = self.stats[i]
                effcoll = tcid / tccol
                speedcoll = effcoll * i

                scalcoll = self.stats[1] / tccol #t-par-1 / t-par-n

                out += "%.10f %.10f %.10f %.10f %.10f %.10f %.10f %.10f %.10f %.10f" % \
                        (tccol, eff, effcoll, speedcm, speedcoll, scalcm,
                         scalcoll, 1/tcid, 1/tc, 1/tccol)
            except KeyError:
                out += "- %.10f - %.10f - %.10f - %.10f %.10f -" % \
                        (eff, speedcm, scalcm, 1/tcid, 1/tc)

            print >>f, out
        f.close()

sizes = (3000, 4000)
seqcom = (711.2548999786, 1274.8331911564)

for s, tseq in zip(sizes, seqcom):
    Plotter(s, tseq).run()
