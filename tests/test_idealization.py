import pytest
import numpy as np

from ascam.core.idealization import Idealizer


test_traces = [
    (
        np.array([1, 1, 1, 2, 2, 3]),
        np.array([[1, 3, 0, 2], [2, 2, 3, 4], [3, 1, 5, 5]]),
    ),
    (
        np.array([2, 1, 1, 2, 2, 3]),
        np.array([[2, 1, 0, 0], [1, 2, 1, 2], [2, 2, 3, 4], [3, 1, 5, 5]]),
    ),
    (
        np.array([2, 1, 1, 2, 2, 3, 3]),
        np.array([[2, 1, 0, 0], [1, 2, 1, 2], [2, 2, 3, 4], [3, 2, 5, 6]]),
    ),
]


@pytest.mark.parametrize("trace, events", test_traces)
def test_extract_events(trace, events):
    out = Idealizer.extract_events(trace, list(range(len(trace))))
    assert np.all(out == events)
