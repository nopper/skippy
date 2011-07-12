# grep scatter * | sed -e "s/^[^-]*\-//" -e "s/ .*//" | awk -F':' '{print $1 ":" $4}'
scatter="""
4000:5.7192800045
4000:5.7373158932
4000:5.7386088371
4000:5.7317960262
4000:5.0946989059
4000:5.2265870571
4000:5.1090250015
5000:8.9389841557
5000:8.9593200684
5000:8.9536890984
5000:8.9535689354
5000:7.9497411251
5000:8.1268100739
5000:8.3394100666
3000:3.2127461433
3000:3.3783619404
3000:3.2193598747
3000:3.2186541557
3000:3.2191331387
3000:2.8589618206
3000:2.9396069050
3000:2.9862549305
3000:3.0550968647
3000:2.9907858372
3000:3.1277430058
3000:2.9632349014
3000:3.0777299404
6000:12.8661968708
6000:12.8983719349
6000:12.8845911026
6000:12.8810150623
6000:12.8918738365
6000:12.8927779198
6000:11.4020721912
6000:11.7458000183
6000:11.9325380325
6000:11.4151041508
"""

results = []
for line in scatter.strip().splitlines():
    dim, time = line.split(':')
    dim = int(dim)
    time = float(time)

    results.append(time / (dim ** 2))

import numpy
arr = numpy.array(results)
print arr.mean()
