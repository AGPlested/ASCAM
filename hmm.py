### Begin setup
import copy
import timeit
import matplotlib.pyplot as plt
import numpy as np
import hmmlearn.hmm as hmm

from sklearn.preprocessing import StandardScaler

from src.utils import piezo_selection
from src import core as ascam
from src.core.idealization import Idealizer

TESTFILE = "data/GluA2_T1_SC-recording_40kHzSR.mat"

def speedtest(f, n_runs, *args, **kwargs):
    def _f():
        return f(*args, **kwargs)
    r = timeit.repeat("_f()", globals=locals(), number=1, repeat=n_runs)
    return min(r), np.mean(r), np.std(r)

def infer(x, model):
    hidden_states = model.predict(x)
    fit = np.zeros_like(x)
    for i in range(len(model.means_)):
        fit[np.where(hidden_states == i)] = model.means_[i]
    return fit

# prepare recording
rec = ascam.Recording.from_file(TESTFILE)
rec.baseline_correction()
rec.gauss_filter_series(1000)

# prepare data
time = rec["BC_GFILTER1000_"][0].time
all_eps = np.concatenate([ep.trace for ep in rec["BC_GFILTER1000_"]])*1e12
# scaler = StandardScaler()
# all_scaled = scaler.fit_transform(all_eps.reshape(-1, 1))
# xs = np.split(all_scaled, np.cumsum([len(ep.trace) for ep in rec["BC_GFILTER1000_"]])[:-1])
xs = np.split(all_eps, np.cumsum([len(ep.trace) for ep in rec["BC_GFILTER1000_"]])[:-1])

# set up model params
n_hidden_states = 5
# System starts in state 0
initial_state_probs = np.zeros(n_hidden_states)
initial_state_probs[0] = 1
amps = np.array([0, -.8, -1.4, -1.8, -2.2])
# scaled_amps = scaler.fit_transform(amps.reshape(-1, 1))

class FixedMeansGaussianHMM(hmm.GaussianHMM):
    def _do_mstep(self, stats):
        """Override the method to avoid updating the means."""
        prev_means = self.means_
        super(FixedMeansGaussianHMM, self)._do_mstep(stats)
        self.means_ = prev_means
# create and fit model
# model = hmm.GaussianHMM(
model = FixedMeansGaussianHMM(
    n_components=n_hidden_states,
    n_iter=10,
    init_params="tc",
)
model.startprob_ = initial_state_probs
model.means_ = amps.reshape(-1, 1)
# model.means_ = scaled_amps
# model.fit(all_scaled)
model.fit(all_eps.reshape(-1, 1))

i = 0

plt.plot(time, xs[i])
plt.plot(time, infer(xs[i].reshape(-1,1), model))
plt.show()
i+=1

# generate plots
for i in range(10):
    plt.clf()
    plt.plot(time, xs[i])
    plt.plot(time, infer(xs[i].reshape(-1,1), model))
    plt.savefig(f"hmmplots/ep_{i}.png")

# generate plots with resolution applied
for i in range(10):
    plt.clf()
    plt.plot(time, xs[i])
    x = infer(xs[i].reshape(-1,1), model).reshape(-1)
    x = Idealizer.apply_resolution(x, time, 5e-5)
    plt.plot(time, x)
    plt.savefig(f"hmmplots/ep_{i}_with_resolution.png")


# try without giving amps
# first time I tried this it found two states on the baseline noise
n_hidden_states = 6
var_mean_model = hmm.GaussianHMM(
    n_components=n_hidden_states,
    n_iter=10,
    init_params="tcm",
)
initial_state_probs = np.zeros(n_hidden_states)
initial_state_probs[0] = 1
var_mean_model.startprob_ = initial_state_probs
var_mean_model.fit(all_eps.reshape(-1, 1))

i = 0

for i in range(10, 15):
    plt.plot(time, xs[i])
    # plt.plot(time, infer(xs[i].reshape(-1,1), var_mean_model))
    x = infer(xs[i].reshape(-1,1), model).reshape(-1)
    x = Idealizer.apply_resolution(x, time, 5e-5)
    plt.plot(time, x)
    plt.show()

