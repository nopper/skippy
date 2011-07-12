import math

# Extracted with cat stats-4000 | grep "to apply on" | awk -F' ' '{print $1 ":" $6}'
stats_3000 = """
1:62.1467659473
2:36.0049271584
4:21.2399849892
5:18.1891689301
6:16.4093370438
8:13.3123631477
10:11.8900120258
12:11.0889959335
15:10.3934650421
16:10.4277060032
18:10.8230249882
20:10.0883309841
24:9.4131009579
"""

stats_4000 = """
1:105.2871079445
2:58.3482208252
4:35.2134659290
5:30.6353340149
8:22.8222448826
10:20.3144469261
16:16.9860851765
"""

stats_5000 = """
1:167.2222020626
2:91.6374499798
4:55.1032249928
5:47.5390081406
8:35.6974570751
10:31.6030290127
16:27.1574308872
"""

stats_6000 = """
1:236.1578409672
2:132.4227020741
3:96.5607550144
4:79.3932199478
5:68.7341182232
6:63.0195581913
8:51.0023219585
10:45.4784460068
12:42.9005050659
16:37.8385479450
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
                   " <efficiency-cm> <efficiency-collected>"                  \
                   " <speed-cm> <speed-coll> <scal-cm> <scal-collected>"      \
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

sizes = (3000, 4000, 5000, 6000)
seqcom = (61.9225819111, 95.8797729015, 146.5988478661, 206.7256488800)

for s, tseq in zip(sizes, seqcom):
    Plotter(s, tseq).run()
