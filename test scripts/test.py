import numpy as np
from time import time, strftime, localtime

EXT_H = 0.005
EXT_L = 0.005
EXT_peri = EXT_H + EXT_L
EXT_NPeri = int(4 / EXT_peri)
EXT_times = [ (i*EXT_peri) for i in range(EXT_NPeri) ] 

t0 = time()
t1 = [EXT_time + t0 for EXT_time in EXT_times]
tn = []
for i in range(EXT_NPeri):
    t2 = strftime("%Y-%m-%dT%H:%M:%S.", localtime(t1[i])) + f"{t1[i] % 1:.3f}".split(".")[1]
    tn.append(t2)
print(len(EXT_times))
print(len(tn))
