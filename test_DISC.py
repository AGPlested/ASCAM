### Begin setup
import timeit
import matplotlib.pyplot as plt
import numpy as np

from src.core.DISC.divisive_segmentation import (
        changepoint_detection)
from src.core.DISC.agglomerative_clustering import agglomorative_clustering_fit
from src.core.DISC import (
        divisive_segmentation, merge_by_ward_distance,
        compare_IC, run_DISC,)
from src.utils import piezo_selection

from src import core as ascam

TESTFILE = "data/GluA2_T1_SC-recording_40kHzSR.mat"

def speedtest(f, n_runs, *args, **kwargs):
    def _f():
        return f(*args, **kwargs)
    r = timeit.repeat("_f()", globals=locals(), number=1, repeat=n_runs)
    return min(r), np.mean(r), np.std(r)

rec = ascam.Recording.from_file(TESTFILE)
rec.baseline_correction()
rec.gauss_filter_series(1000)

rec.keys()

### Finish setup
#------------------------------------------------------------
### Start testing stuff

ep = rec["BC_GFILTER1000_"][0]
plt.plot(ep.time, ep.trace)
plt.title("Baseline corrected and Gauss filtered at 1kHz")
plt.show()
x = ep.trace

# Full DISC over data
BM = "full"
plt.plot(ep.time, x, label="data")
y = run_DISC(x, confidence_level=1e-15, BIC_method=BM)
plt.plot(ep.time, y, label="DISC")
title = "DISC with our BIC implementation"
plt.title(title)
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Full DISC over data
BM = "approx"
plt.plot(ep.time, x, label="data")
y = run_DISC(x, confidence_level=1e-15, BIC_method=BM)
plt.plot(ep.time, y, label="DISC")
title = "DISC with the matlab BIC implementation"
plt.title(title)
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Comparison of cp-detection confidence levels
plt.plot(ep.time, x, label="data", alpha=0.2)
y, _ = changepoint_detection(x, confidence_level=1e-15)
plt.plot(ep.time, y, label="CP 1e-15")
z, _ = changepoint_detection(x, confidence_level=1e-1)
plt.plot(ep.time, z, label="CP 1e-1")
title = "Effect of α-value in change point detection"
plt.title(title)
plt.legend()
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

n_runs = 100
timeit.timeit("changepoint_detection(x, confidence_level=1e-15)", globals=locals(), number=n_runs)
# result a=7.204387945996132
timeit.timeit("divisive_segmentation(x, confidence_level=1e-15, BIC_method='approx')", globals=locals(), number=n_runs)
# result b=33.081147256991244
# i.e. 4.6 times as long

# Comparison of cp-detection and divseg
plt.plot(ep.time, x, label="data", alpha=0.2)
y, _ = changepoint_detection(x, confidence_level=1e-15)
plt.plot(ep.time, y, label="CP 1e-15")
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method="approx")
plt.plot(ep.time, y, label="divisive segmentation")
title = "Improvement of divisive segmentation over changepoint detection"
plt.title(title)
plt.legend()
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Compare BIC methods in divseg
BM="approx"
plt.plot(ep.time, x, label="data", alpha=0.2)
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method=BM)
plt.plot(ep.time, y, label=BM)
BM="full"
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method=BM)
plt.plot(ep.time, y, label=BM)
title = "divisive segmentation with different BIC methods"
plt.title(title)
plt.legend()
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Compare divseg result to AC result
BM="approx"
plt.plot(ep.time, x, label="data", alpha=0.2)
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method=BM)
plt.plot(ep.time, y, label="divseg")
y = agglomorative_clustering_fit(x, y, BIC_method=BM)
plt.plot(ep.time, y, label="AC")
title = f"Divisive segmentation vs agglomerative clustering using '{BM}' method"
plt.title(title)
plt.legend()
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Compare divseg result to AC result
BM="approx"
plt.plot(ep.time, x, label="data", alpha=0.2)
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method=BM)
plt.plot(ep.time, y, label="divseg")
y = agglomorative_clustering_fit(x, y, BIC_method=BM)
plt.plot(ep.time, y, label="AC")
title = f"Divisive segmentation vs agglomerative clustering using '{BM}' method"
plt.title(title)
plt.legend()
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Compare divseg result to AC result
BM="full"
plt.plot(ep.time, x, label="data", alpha=0.2)
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method=BM)
plt.plot(ep.time, y, label="divseg")
y = agglomorative_clustering_fit(x, y, BIC_method=BM)
plt.plot(ep.time, y, label="AC")
title = f"Divisive segmentation vs agglomerative clustering using '{BM}' method"
plt.title(title)
plt.legend()
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Compare AC to DISC
BM="approx"
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method=BM)
y = agglomorative_clustering_fit(x, y, BIC_method=BM)
plt.plot(ep.time, y, label="AC")
y = run_DISC(x, confidence_level=1e-15, min_seg_length=3, BIC_method=BM)
plt.plot(ep.time, y, label="DISC")
plt.plot(ep.time, x, label="data", alpha=0.2)
title = f"AC vs DISC using {BM} BIC"
plt.title(title)
plt.legend()
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Compare AC to DISC
BM="full"
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method=BM)
y = agglomorative_clustering_fit(x, y, BIC_method=BM)
plt.plot(ep.time, y, label="AC")
y = run_DISC(x, confidence_level=1e-15, min_seg_length=3, BIC_method=BM)
plt.plot(ep.time, y, label="DISC")
plt.plot(ep.time, x, label="data", alpha=0.2)
title = f"AC vs DISC using {BM} BIC"
plt.title(title)
plt.legend()
# plt.show()
plt.savefig(f"../disc_plots/{title}")
plt.close()

# Compare DISC execution speed between BIC methods
n_runs = 100
rf = timeit.repeat('run_DISC(x, confidence_level=1e-15, BIC_method="full")', globals=locals(), number=1, repeat=n_runs)
# min(rf) = 0.380776509991847
ra = timeit.repeat('run_DISC(x, confidence_level=1e-15, BIC_method="approx")', globals=locals(), number=1, repeat=n_runs)
# min(ra) = 0.4044556239969097

# Evaluate DISC speed on entire recording
def DISC_on_rec(ep_list, BM):
    out = []
    for ep in ep_list:
        out.append(run_DISC(ep.trace, confidence_level=1e-15, BIC_method=BM))
    return out

r = timeit.repeat('DISC_on_rec(rec["BC_GFILTER1000_"], "full")', globals=locals(), number=1, repeat=5)
# min(r) = 41.23737898300169,

BM = "approx"
BM = "full"
y, _ = divisive_segmentation(x, confidence_level=1e-15, BIC_method=BM)
all_data_fits = merge_by_ward_distance(y)
best_fit_ind = compare_IC(x, all_data_fits, BIC_method=BM)

plt.plot(ep.time, x, alpha=0.2)
plt.plot(ep.time, all_data_fits[:,3], label= f"3 states")
plt.legend()
# plt.show()
plt.savefig("../disc_plots/intermediate3states_full.png")
plt.close()

plt.plot(ep.time, x, alpha=0.2)
plt.plot(ep.time, all_data_fits[:,4], label= f"4 states")
plt.legend()
# plt.show()
plt.savefig("../disc_plots/intermediate4states_full.png")
plt.close()

plt.plot(ep.time, x, alpha=0.2)
plt.plot(ep.time, all_data_fits[:,5], label= f"5 states")
plt.legend()
# plt.show()
plt.savefig("../disc_plots/intermediate5states_full.png")
plt.close()


# concatentate all episodes
all_eps = np.concatenate([ep.trace for ep in rec["BC_GFILTER1000_"]])

#run full DISC on concatenated data and measre execution time
BM = "full"
Y_full = run_DISC(all_eps, confidence_level=1e-15, BIC_method=BM)
# finds 4 unique states
# partition the output into individual episodes
ys = np.split(y, np.cumsum([len(ep.trace) for ep in rec["BC_GFILTER1000_"]])[:-1])
i =3
x = rec["BC_GFILTER1000_"][i].trace
y = ys[i]
plt.plot(ep.time, x, alpha=0.2)
plt.plot(ep.time, y)
plt.show()

speedtest(run_DISC, 1, all_eps, confidence_level=1e-15, BIC_method="full")
# ~ 120s

BM = "approx"
Y_approx = run_DISC(all_eps, confidence_level=1e-15, BIC_method=BM)
# finds 23 unique states
ys = Y_approx.reshape(-1, len(ep.trace))
i = 3
x = rec["BC_GFILTER1000_"][i].trace
y = ys[i]
plt.plot(ep.time, x, alpha=0.2)
plt.plot(ep.time, y)
plt.show()

speedtest(run_DISC, 1, all_eps, confidence_level=1e-15, BIC_method="approx")
# ~ 320s

# Try working with the parts of the episodes that are actually in glutamate
data_in_piezo = [ep.filter_by_piezo() for ep in rec["BC_GFILTER1000_"]]

i+=1
# plot the selected part of the first episode
time, trace = data_in_piezo[i]
plt.plot(time, trace)
# plot the entire episode with alpha=0.2
plt.plot(rec["BC_GFILTER1000_"][i].time, rec["BC_GFILTER1000_"][i].trace, alpha=0.2)
# plot the piezo voltage in a second axis
plt.twinx()
plt.plot(rec["BC_GFILTER1000_"][i].time, rec["BC_GFILTER1000_"][i].piezo, color="red", alpha=0.2)
plt.show()

# concatenate all the active parts of all episodes
all_eps_active = np.concatenate([ep[1] for ep in data_in_piezo])

speedtest(run_DISC, n_runs, all_eps_active, confidence_level=1e-15, BIC_method="full")
# 39s

speedtest(run_DISC, n_runs, all_eps_active, confidence_level=1e-15, BIC_method="approx")
# 90s


## Check execution time on all data using with BIC methods and with/without
## filtering by piezo
all_eps_active = np.concatenate([ep.filter_by_piezo()[1] for ep in rec["BC_GFILTER1000_"]])
all_eps = np.concatenate([ep.trace for ep in rec["BC_GFILTER1000_"]])
mint, meant, stdt = speedtest(run_DISC, 5, all_eps, confidence_level=1e-15, BIC_method="full")
print(f"All data using 'full': {mint:.2f} s, {meant:.2f} s, {stdt:.2f} s")
# All data using 'full': 110.13 s, 123.32 s, 8.65 s
mint, meant, stdt = speedtest(run_DISC, 5, all_eps, confidence_level=1e-15, BIC_method="approx")
print(f"All data using 'approx': {mint:.2f} s, {meant:.2f} s, {stdt:.2f} s")
# All data using 'approx': 331.57 s, 362.49 s, 28.94 s
mint, meant, stdt = speedtest(run_DISC, 10, all_eps_active, confidence_level=1e-15, BIC_method="full")
print(f"Data in pieze using 'full': {mint:.2f} s, {meant:.2f} s, {stdt:.2f} s")
# Data in pieze using 'full': 27.48 s, 29.15 s, 1.75 s
mint, meant, stdt = speedtest(run_DISC, 10, all_eps_active, confidence_level=1e-15, BIC_method="approx")
print(f"Data in pieze using 'approx': {mint:.2f} s, {meant:.2f} s, {stdt:.2f} s")
# Data in pieze using 'approx': 85.47 s, 86.97 s, 0.88 s
