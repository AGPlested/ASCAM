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
        np.array([2,2,2,2,1,2,3,3,3,4,6,6,6,6,6,6,1,1,1,1 , 1, 2, 2, 3, 2,2,2,2,5,5,5,5,5,5,3]),
    ),
    (
        4,
        np.array([2, 1, 1, 2, 2, 3, 3,3,3,3,3,3,3, 5,5,5,5,5, 2,2,2,2,2,2,2, 1,1,1,1,1,1,1]),
    ),
    (
        4,
        np.array([2, 1, 1, 2, 2, 3, 3]),
    ),
]


@pytest.mark.parametrize("resolution, trace", resolution_test_event_series)
def test_extract_events_with_resolution(resolution, trace):
    idealization = Idealizer.apply_resolution(trace, np.arange(len(trace)), resolution)
    out = Idealizer.extract_events(idealization, np.arange(len(idealization)))
    assert np.all(out[:, 1] >= resolution)

@pytest.mark.parametrize("trace, events", test_traces)
def test_extract_events(trace, events):
    out = Idealizer.extract_events(trace, np.arange(len(trace)))
    print(out)
    print(events)
    assert np.all(out == events)
