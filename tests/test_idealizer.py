import pytest
import numpy as np

from src.core.idealization import Idealizer

# (trace, events)
test_traces = [
    (
        np.array([1, 1, 2, 1, 1, 1], dtype=float),
        np.array([[1, 2, 0, 1],
                  [2, 1, 2, 2],
                  [1, 3, 3, 5]], dtype=float),
    ),
    (
        np.array([1, 1, 1, 2, 2, 3], dtype=float),
        np.array([[1, 3, 0, 2],
                  [2, 2, 3, 4],
                  [3, 1, 5, 5]], dtype=float),
    ),
    (
        np.array([2, 1, 1, 2, 2, 3], dtype=float),
        np.array([[2, 1, 0, 0],
                  [1, 2, 1, 2],
                  [2, 2, 3, 4],
                  [3, 1, 5, 5]], dtype=float),
    ),
    (
        np.array([2, 1, 1, 2, 2, 3, 3], dtype=float),
        np.array([[2, 1, 0, 0],
                  [1, 2, 1, 2],
                  [2, 2, 3, 4],
                  [3, 2, 5, 6]], dtype=float),
    ),
]

resolution_test_event_series = [
    (
        2,
        np.array([1, 1, 1, 2, 2, 3]),
    ),
    (
        2,
        np.array([2, 1, 1, 2, 2, 3]),
    ),
    (
        4,
        np.array([2, 2, 2, 2, 1, 2, 3, 3, 3, 4, 6, 6, 6, 6, 6, 6, 1,
                 1, 1, 1, 1, 2, 2, 3, 2, 2, 2, 2, 5, 5, 5, 5, 5, 5, 3]),
    ),
    (
        4,
        np.array([2, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 5, 5, 5,
                 5, 5, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1]),
    ),
    (
        4,
        np.array([2, 1, 1, 2, 2, 3, 3]),
    ),
]


@pytest.mark.parametrize("resolution, trace", resolution_test_event_series)
def test_extract_events_with_resolution(resolution, trace):
    idealization = Idealizer.apply_resolution(
        trace, np.arange(len(trace)), resolution)
    out = Idealizer.extract_events(idealization, np.arange(len(idealization)))
    assert np.all(out[:, 1] >= resolution)


@pytest.mark.parametrize("trace, events", test_traces)
def test_extract_events(trace, events):
    out = Idealizer.extract_events(trace, np.arange(len(trace)))
    assert np.allclose(out, events)


def test_single_amplitude():
    # Test case with only one amplitude
    signal = np.random.rand(100)
    amplitudes = np.array([1])
    idealization = Idealizer.threshold_crossing(signal, amplitudes)
    assert np.allclose(idealization, np.ones(100))


def test_two_amplitudes():
    # Test case with default thresholds
    signal = np.random.rand(100)
    amplitudes = np.array([0, 1])
    idealization = Idealizer.threshold_crossing(signal, amplitudes)
    assert np.all([np.isclose(i, 0) or np.isclose(i, 1) for i in idealization])


def test_custom_thresholds():
    # Test case with custom thresholds
    signal = np.random.rand(100)
    amplitudes = np.array([1, 2, 3])
    thresholds = np.array([0.5, 1.8])
    idealization = Idealizer.threshold_crossing(signal, amplitudes, thresholds)
    assert np.all([np.isclose(i, 1) or np.isclose(i, 3)
                  or np.isclose(i, 2) for i in idealization])


def test_wrong_thresholds():
    # Test case with wrong number of thresholds
    signal = np.random.rand(100)
    amplitudes = np.array([1, 2, 3])
    thresholds = np.array([0.5, 0.8, 0.9])
    with pytest.raises(ValueError):
        Idealizer.threshold_crossing(signal, amplitudes, thresholds)


@pytest.fixture
def correct_amplitudes():
    return np.array(range(0, 5))


def test_threshold_crossing(signal_trunc_noise, correct_amplitudes, true_signal):
    # Test case with default thresholds
    idealization = Idealizer.threshold_crossing(signal_trunc_noise(),
                                                correct_amplitudes)
    assert np.allclose(idealization, true_signal())


def test_idealize_episode_TC(signal_trunc_noise, correct_amplitudes,
                             time, true_signal):
    # Test case with default thresholds
    idealization, _ = Idealizer.TC_idealize_episode(signal_trunc_noise(), time(),
                                                    correct_amplitudes)
    assert np.allclose(idealization, true_signal())


def test_idealize_episode_with_method_TC(signal_trunc_noise, correct_amplitudes,
                                         time, true_signal):
    params = {"amplitudes": correct_amplitudes}
    idealization, _ = Idealizer.idealize_trace(signal_trunc_noise(),
                                                 time(), method="TC",
                                                 params=params
                                                 )
    assert np.allclose(idealization, true_signal())

BIC_methods_values = ["full", "approx"]
@pytest.mark.parametrize("BIC_method", BIC_methods_values)
def test_idealize_trace_DISC(signal_trunc_noise, BIC_method):
    """Since DISC output is harder to predict we only check if the
    output is of the correct shape."""
    idealization = Idealizer.DISC_idealize_trace(signal_trunc_noise(),
                                                BIC_method=BIC_method)
    assert idealization.shape == signal_trunc_noise().shape

pieze_selection_values = [True, False]
@pytest.mark.parametrize("piezo_selection", pieze_selection_values)
def test_idealize_episode_DISC(recording, piezo_selection):
    """Since DISC output is harder to predict we only check if the
    output is of the correct shape."""
    time, idealization = Idealizer.DISC_idealize_episode(recording.episode(),
                                                piezo_selection=piezo_selection)
    if piezo_selection:
        eptime, trace = recording.episode().filter_by_piezo()
        assert idealization.shape == trace.shape
        assert time.shape == eptime.shape
    else:
        assert idealization.shape == recording.episode().trace.shape

datakey_values = ["raw_", None]
@pytest.mark.parametrize("datakey", datakey_values)
def test_idealize_recording_DISC(recording, datakey):
    """Since DISC output is harder to predict we only check if the
    output is of the correct shape.
    Use `BIC_method="full"` and `piezo_selection=True` because it is faster."""
    _, idealization = Idealizer.DISC_idealize_recording(
        recording, datakey=datakey, BIC_method="full", piezo_selection=True)
    if datakey is not None:
        _, conc_trace = recording.concatenated_series_by_datakey(
            datakey=datakey).filter_by_piezo()
    else:
        _, conc_trace = recording.concatenated_series.filter_by_piezo()
    assert idealization.shape == conc_trace.shape


# def test_idealize_episode_with_method_DISC(signal_trunc_noise, correct_amplitudes,
#                                          time, true_signal):
#     params = {"alpha" : 0.05, "min_seg_length" : 3, "min_cluster_size" : 3,
#               "IC_div_seg" : "BIC", "IC_HAC" : "BIC", "BIC_method" : "full", }
#     idealization, _ = Idealizer.idealize_episode(signal_trunc_noise(),
#                                                  time(), method="DISC",
#                                                  params=params
#                                                  )
#     assert np.allclose(idealization, true_signal())
