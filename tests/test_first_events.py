#!/usr/bin/env python3

from src.core.analysis import detect_first_events
import numpy as np


def test_detect_first_events():
    idealizedTraces = (
        -np.hstack(
            [np.zeros(1010), np.ones(500), 2*np.ones(800), np.zeros(700)]
        ),  # normal trace
        -np.hstack(
            [np.ones(310), np.zeros(700), np.ones(500), 2*np.ones(800), np.zeros(700)]
        ),  # baseline event
        -np.hstack(
            [np.zeros(1010), 2*np.ones(500), np.ones(800), np.zeros(700)]
        ),  # open to O2
        -np.hstack(
            [np.zeros(1010), np.ones(1300), np.zeros(700)]
        ),  # not all visited
    )
    time = np.linspace(0, 100, 3010)*1e-3
    piezo = np.hstack([np.zeros(500), 4*np.ones(1510), np.zeros(1000)])
    states = -np.array([0.0, 1.0, 2.0])
    threshold = -0.5
    first_activations = []
    first_events_list = []
    for idealizedTrace in idealizedTraces:
        trace = idealizedTrace + (np.random.rand(3010) - 0.5)*1e-3
        first_activation, first_events = detect_first_events(
            time, trace*1e-12, threshold, piezo, idealizedTrace, states
        )
        first_activations.append(first_activation)
        first_events_list.append(first_events)
    starttimes = np.hstack([first_events[0, :] for first_events in first_events_list])
    assert all(starttimes[~np.isnan(starttimes)] >= first_activation)
    assert all(starttimes[~np.isnan(starttimes)] >= time[np.argmax(piezo == 4)])
    assert all(np.isnan(first_events_list[3][:, -1]))
    assert len(starttimes[np.isnan(starttimes)]) == 1
    assert first_events_list[2][1, 2] < first_events_list[2][1, 1]
