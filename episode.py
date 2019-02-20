import logging

import numpy as np
import matplotlib.pyplot as plt

from filtering import gaussian_filter, ChungKennedyFilter
from analysis import (baseline_correction, threshold_crossing,
                        detect_first_activation)
from tools import piezo_selection, parse_filename, interval_selection

class Episode():
    def __init__(self, time, trace, n_episode=0, piezo=None, command=None,
                 sampling_rate=4e4, time_unit='ms', piezo_unit='V',
                 command_unit='mV', trace_unit='pA', input_time_unit='s'):
        """
        Episode objects hold all the information about an epoch and
        should be used to store raw and manipulated data

        Parameters:
            time [1D array of floats] - containing time (in seconds)
            trace [1D array of floats] - containing the current
                                                trace
            piezo [1D array of floats] - the voltage applied to the
                                         Piezo device
            command [1D array of floats] - voltage applied to
                                                  cell
            n_episode [int] - the number of measurements on this cell that
                          came before this one
            filterType [string] - type of filter used
        """
        # units of the data
        # the units of the private attributes (eg _time) should be SI units
        # ie seconds, ampere etc
        self.time_unit = time_unit
        self.time_unit_factors = {'ms':1e3, 's':1}
        self.trace_unit = trace_unit
        self.trace_unit_factors = {'fA':1e15, 'pA':1e12, 'nA':1e9, 'µA':1e6,
                                    'mA':1e3, 'A':1}
        self.command_unit = command_unit
        self.command_unit_factors = {'uV':1e6, 'mV':1e3, 'V':1}
        self.piezo_unit = piezo_unit
        self.piezo_unit_factors = {'uV':1e6, 'mV':1e3, 'V':1}
        # units when given input
        input_time_unit_factors = {'ms':1e-3, 's':1}
        input_time_factor = input_time_unit_factors[input_time_unit]
        # private attributes storing the actual data
        self._time = time*input_time_factor
        self._trace = trace
        self._piezo = piezo
        self._command = command
        # results of analyses
        self._first_activation = None
        self._idealization = None
        # metadata about the episode
        self.n_episode = int(n_episode)
        self.sampling_rate = sampling_rate
        self.suspiciousSTD = False

    @property
    def time(self):
        if self._time is not None:
            return self._time*self.time_unit_factor
        else: return None

    @property
    def trace(self):
        if self._trace is not None:
            return self._trace*self.trace_unit_factor
        else: return None

    @property
    def piezo(self):
        if self._piezo is not None:
            return self._piezo*self.piezo_unit_factor
        else: return None

    @property
    def command(self):
        if self._command is not None:
            return self._command*self.command_unit_factor
        else: return None

    @property
    def first_activation(self):
        if self._first_activation is not None:
            return self._first_activation*self.time_unit_factor
        else: return None

    @first_activation.setter
    def first_activation(self, fa):
        self._first_activation = fa/self.time_unit_factor

    @property
    def idealization(self):
        if self._idealization is not None:
            return self._idealization*self.trace_unit_factor
        else: return None

    @idealization.setter
    def idealization(self, id):
        self._idealization = id

    @property
    def time_unit_factor(self): return self.time_unit_factors[self.time_unit]

    @property
    def trace_unit_factor(self): return self.trace_unit_factors[self.trace_unit]

    @property
    def command_unit_factor(self):
        return self.command_unit_factors[self.command_unit]

    @property
    def piezo_unit_factor(self): return self.piezo_unit_factors[self.piezo_unit]

    def gauss_filter_episode(self, filter_frequency=1e3, method='convolution'):
        """Replace the current trace of the episode by the gauss filtered
        version of itself."""

        self._trace = gaussian_filter(signal=self._trace,
                                     filter_frequency=filter_frequency,
                                     sampling_rate=self.sampling_rate)
        # reset idealization
        self._idealization = None

    def CK_filter_episode(self, window_lengths, weight_exponent, weight_window,
				          apriori_f_weights=False, apriori_b_weights=False):
        """Replace the current _trace by the CK fitered version of itself."""

        ck_filter = ChungKennedyFilter(window_lengths, weight_exponent,
                            weight_window, apriori_f_weights, apriori_b_weights)
        self._trace = ck_filter.apply_filter(self._trace)
        # reset _idealization
        self._idealization = None

    def baseline_correct_episode(self, intervals, method='poly', degree=1,
                                 select_intvl=False, select_piezo=False,
                                 active=False, deviation=0.05):
        """Apply a baseline correction to the episode."""

        self._trace = baseline_correction(time=self._time, signal=self._trace,
                                         fs=self.sampling_rate,
                                         intervals=intervals,
                                         degree=degree, method=method,
                                         select_intvl=select_intvl,
                                         piezo=self._piezo,
                                         select_piezo=select_piezo,
                                         active=active, deviation=deviation)
        # reset _idealization
        self._idealization = None

    def idealize(self, amplitudes, thresholds):
        """Idealize the episode using threshold crossing."""

        self._idealization = threshold_crossing(self._trace, amplitudes,
                                                thresholds)

    def check_standarddeviation_all(self, stdthreshold=5e-13):
        """Check the standard deviation of the episode against a reference
        value."""

        _, _, trace = piezo_selection(self._time, self._piezo,
                                      self._trace, active = False,
                                      deviation = 0.01)
        tracestd = np.std(trace)
        if tracestd>stdthreshold:
            self.suspiciousSTD = True

    def get_command_stats(self):
        """Get the mean and standard deviation of the command voltage of the
        episode."""

        try:
            mean = np.mean(self._command)
            std = np.std(self._command)
        except:
            mean = std = np.nan
        return mean, std

    def detect_first_activation(self, threshold):
        """Detect the first activation in the episode."""

        self._first_activation = detect_first_activation(self._time,
                                                         self._trace,
                                                         threshold)

    def get_events(self):
        """Get the events (i.e. states) from the idealized trace.

        Assumes time and trace to be of equal length and time to start not at 0
        Returns:
            a table containing the amplitude of an opening, its start and end
            time and its duration"""

        diff = self.idealization[1:]-self.idealization[:-1]
        events = np.where(diff!=0)[0]
        # diff+1 marks the indices of the first time point of a new event
        # starting from 0 to diff[0] is the first event, and from diff[-1] to
        # t_end is the last event, hence
        n_events = events.size+1
        # init the array they will be final output table, events in rows and
        # amplitude, start, end and duration in columns
        event_list = np.zeros((n_events,4))
        # fill the array
        if n_events == 1:
            event_list[0][0] = self.idealization[0]
            event_list[0][2] = self.time[0]-(self.time[1]-self.time[0])
            event_list[0][3] = self.time[-1]
        else:
            event_list[0][0] = self.idealization[0]
            event_list[0][2] = self.time[0]-(self.time[1]-self.time[0])
            event_list[0][3] = self.time[int(events[0])]
            for i, t in enumerate(events[:-1]):
                event_list[i+1][0] = self.idealization[int(t)+1]
                event_list[i+1][2] = self.time[int(events[i])]
                event_list[i+1][3] = self.time[int(events[i+1])]
            event_list[-1][0] = self.idealization[int(events[-1])+1]
            event_list[-1][2] = self.time[(int(events[-1]))]
            event_list[-1][3] = self.time[-1]
        # get the duration column
        event_list[:,1]=event_list[:,3]-event_list[:,2]
        return event_list
