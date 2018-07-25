import numpy as np

from filtering import gaussian_filter, ChungKennedyFilter
from analysis import baseline_correction, threshold_crossing, multilevel_threshold
from tools import piezo_selection, parse_filename

class Episode():
    def __init__(self, time, trace, n_episode=0, piezo=None, command=None,
                 filterType=None, sampling_rate=4e4, timeInputUnit='ms'):
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
        time_unit_multiplier = 1
        if timeInputUnit=='ms': time_unit_multiplier = 1000

        self.time = time*time_unit_multiplier
        self.trace = trace
        self.piezo = piezo
        self.command = command
        self.n_episode = int(n_episode)
        self.sampling_rate = sampling_rate
        self.suspiciousSTD = False

    def gauss_filter_episode(self, filterFrequency=1e3, method='convolution'):
        """
        Replace the current trace of the episode by the gauss filtered version
        of itself
        """
        self.trace = gaussian_filter(signal=self.trace,
                                     filterFrequency=filterFrequency,
                                     sampling_rate=self.sampling_rate)

    def CK_filter_episode(self, window_lengths, weight_exponent, weight_window,
				          apriori_f_weights=False, apriori_b_weights=False):
        """
        Replace the current trace by the CK fitered version of itself
        """
        ck_filter = ChungKennedyFilter(window_lengths, weight_exponent,
                            weight_window, apriori_f_weights, apriori_b_weights)
        self.trace = ck_filter.apply_filter(self.trace)

    def baseline_correct_episode(self, intervals, method='poly', degree=1,
                                 time_unit='ms', select_intvl=False,
                                 select_piezo=False, active=False,
                                 deviation=0.05):
        self.trace = baseline_correction(time=self.time, signal=self.trace,
                                         fs=self.sampling_rate,
                                         intervals=intervals,
                                         degree=degree, method=method,
                                         time_unit=time_unit,
                                         select_intvl=select_intvl,
                                         piezo=self.piezo,
                                         select_piezo=select_piezo,
                                         active=active, deviation=deviation)

    def idealize(self, mode='thresholds', *args, **kwargs):
        if mode=='levels':
            self.trace = threshold_crossing(self.trace, *args)
        elif mode=='thresholds':
            self.trace = multilevel_threshold(self.trace, *args, **kwargs)

    def check_standarddeviation_all(self, stdthreshold=5e-13):
        """
        check the standard deviation of the episode against a reference value
        """
        _, _, trace = piezo_selection(self.time, self.piezo,
                                      self.trace, active = False,
                                      deviation = 0.01)
        tracestd = np.std(trace)
        if tracestd>stdthreshold:
            self.suspiciousSTD = True

    def get_command_stats(self):
        """
        Get the mean and standard deviation of the command voltage of the
        episode
        """
        try:
            mean = np.mean(self.command)
            std = np.std(self.command)
        except:
            mean = std = np.nan
        return mean, std
