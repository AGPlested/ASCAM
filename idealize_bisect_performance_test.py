import timeit
import numpy as np
import scipy as sp

from src import core as ascam

from src.core.DISC.divisive_segmentation import idealize_bisect

TESTFILE = "data/GluA2_T1_SC-recording_40kHzSR.mat"

rec = ascam.Recording.from_file(TESTFILE)
rec.baseline_correction()
rec.gauss_filter_series(1000)

ep = rec["BC_GFILTER1000_"][0]
x = ep.trace

N = len(x)
confidence_level = 1e-15
crit_val = sp.stats.t.ppf(q=1-confidence_level/2, df=N-1)
# Estimate standard deviation of noise in x.
sorted_wavelet = np.sort(abs(np.diff(x) / 1.4))
noise_std = sorted_wavelet[round(0.682 * (N-1))]

# NOn-recurisve version of the above function.
def idealize_bisect_nonrecursive(data, critical_value, noise_std,
                                    min_seg_length=3):
    N = len(data)
    id_bisect = np.zeros(N)
    # Initialize stack with the entire data array.
    stack = [(0, N-1)]
    while stack:
        start, end = stack.pop()
        # Find bisecting change point using t-test.
        t, cp = t_test_changepoint_detection(data[start:end+1], noise_std)
        # If t-statistic is significant bisect data at change point and
        # recursively look for change points in the resulting segments.
        if (cp is not None and t >= critical_value
            and cp+1 >= min_seg_length and end-cp >= min_seg_length):
            # cp is the index of the last element of `data` belonging to
            # the segment. Since python indexing uses right-open intervals
            # we need to use cp+1 to capture the entire segment.
            stack.append((start, start+cp))
            stack.append((start+cp+1, end))
        else:
            id_bisect[start:end+1] = np.mean(data[start:end+1])
    return id_bisect

#gtp version
def idealize_bisect_gpt(data, critical_value, noise_std, min_seg_length=3):
    segments = [(0, len(data))]
    output = np.empty(len(data))

    while segments:
        start, end = segments.pop()
        segment_data = data[start:end]

        t, cp = t_test_changepoint_detection(segment_data, noise_std)

        if (cp is not None and t >= critical_value
            and cp+1 >= min_seg_length and len(segment_data)-cp-1 >= min_seg_length):
            # cp is the index of the last element of `data` belonging to the
            # segment. Since python indexing uses right-open intervals we need
            # to use cp+1 to capture the entire segment.
            first_segment_end = start + cp + 1
            segments.append((start, first_segment_end))
            segments.append((first_segment_end, end))
        else:  # If t is not significant, return data idealized to mean value.
            output[start:end] = np.mean(segment_data)

    return output


n_runs = 1000
# run idealize_bisect and time it
r1 = timeit.repeat('idealize_bisect(x, crit_val, noise_std)', globals=locals(), number=1, repeat=n_runs)
print(f"idealize_bisect Min execution time {min(r1)}, mean time {np.mean(r1)}, std {np.std(r1)}")

# run idealize_bisect_nonrecursive and time it
r2 = timeit.repeat('idealize_bisect_nonrecursive(x, crit_val, noise_std)', globals=locals(), number=1, repeat=n_runs)
print(f"idealize_bisect_nonrecursive Min execution time {min(r2)}, mean time {np.mean(r2)}, std {np.std(r2)}")

# run idealize_bisect_gpt and time it
r3 = timeit.repeat('idealize_bisect_gpt(x, crit_val, noise_std)', globals=locals(), number=1, repeat=n_runs)
print(f"idealize_bisect_gpt Min execution time {min(r3)}, mean time {np.mean(r3)}, std {np.std(r3)}")

# Over 1000 runs on a single episode, the recursive version is 10% faster than the non-recursive version.
# idealize_bisect Min execution time 0.08119018498109654, mean time 0.09304065229441039, std 0.010073602240927912
# idealize_bisect_nonrecursive Min execution time 0.07977666502119973, mean time 0.09091722270369064, std 0.009012273759944456
# idealize_bisect_gpt Min execution time 0.08048018399858847, mean time 0.0939001920367591, std 0.008962971555070798

x = np.concatenate([ep.trace for ep in rec["BC_GFILTER1000_"]])
n_runs = 10

r1 = timeit.repeat('idealize_bisect(x, crit_val, noise_std)', globals=locals(), number=1, repeat=n_runs)
print(f"idealize_bisect Min execution time {min(r1)}, mean time {np.mean(r1)}, std {np.std(r1)}")

# run idealize_bisect_nonrecursive and time it
r2 = timeit.repeat('idealize_bisect_nonrecursive(x, crit_val, noise_std)', globals=locals(), number=1, repeat=n_runs)
print(f"idealize_bisect_nonrecursive Min execution time {min(r2)}, mean time {np.mean(r2)}, std {np.std(r2)}")

# run idealize_bisect_gpt and time it
r3 = timeit.repeat('idealize_bisect_gpt(x, crit_val, noise_std)', globals=locals(), number=1, repeat=n_runs)
print(f"idealize_bisect_gpt Min execution time {min(r3)}, mean time {np.mean(r3)}, std {np.std(r3)}")

# Over 10 runs on all data, the recursive version is faster than the non-recursive version.
# idealize_bisect Min execution time 23.06771813001251, mean time 25.58793835940305, std 1.4044733949377797
# print('\a')
# idealize_bisect_nonrecursive Min execution time 25.931310084997676, mean time 28.847218118899036, std 2.8552667199472834
# idealize_bisect_gpt Min execution time 26.537214942043647, mean time 27.20225502270041, std 0.4039689047072716
