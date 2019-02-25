import numpy as np

from tools import interval_selection, piezo_selection


class Idealizer():
    @classmethod
    def idealize_episode(cls, signal, amplitudes, thresholds=np.array([]),
                         resolution=None, time=None):
        """Get idealization for single episode."""

        idealizer = cls(amplitudes, thresholds)
        idealization = idealizer.threshold_crossing(signal)
        if resolution is not None:
            idealization = idealizer.apply_resolution(idealization, time,
                                                      resolution)
        return idealization

    def __init__(self, amplitudes, thresholds=np.array([])):
        """Container object for the different idealization functions.

        Arguments:
            amplitudes [1D numpy array] - supposed true amplitudes of signal
            thresholds [1D numpy array] - thresholds between the amplitudes
        If the wrong number of thresholds (or none) are given they will be replaced
        by the midpoint between the pairs of adjacent amplitudes."""

        self.amplitudes = np.asarray(amplitudes)
        self.amplitudes.sort()
        self.amplitudes = self.amplitudes[::-1]
        if self.amplitudes.size == 1:
            return np.ones(signal.size)*self.amplitudes
        if thresholds.size != self.amplitudes.size - 1:
            self.thresholds = (self.amplitudes[1:]+self.amplitudes[:-1]) / 2
        else: self.thresholds = thresholds

    def threshold_crossing(self, signal):
        """Perform a threshold-crossing idealization on the signal.

        Arguments:
            signal [1D numpy array] - data to be idealized"""

        self.amplitudes = np.asarray(self.amplitudes)
        self.amplitudes.sort()
        self.amplitudes = self.amplitudes[::-1]
        if self.amplitudes.size == 1:
            return np.ones(signal.size)*self.amplitudes
        if self.thresholds.size != self.amplitudes.size - 1:
            self.thresholds = (self.amplitudes[1:]+self.amplitudes[:-1]) / 2

        idealization = np.zeros(len(signal))
        # np.where returns a tuple containing array so we have to get the first
        # element to get the indices
        inds = np.where(signal>self.thresholds[0])[0]
        idealization[inds] = self.amplitudes[0]

        for thresh, amp in zip(self.thresholds, self.amplitudes[1:]):
            inds = np.where(signal<thresh)[0]
            idealization[inds] = amp
        return idealization

    def apply_resolution(self, idealization, time, resolution):
        """Remove from the idealization any events that are too short.

        Args:
            idealization [1D numpy array] - an idealized current trace
            time [1D numpy array] - the corresponding time array
            resolution [int] - the minimum duration for an event"""

        events = self.extract_events(idealization, time)

        for i, dur in enumerate(events[:,1]):
            if dur < resolution:
                i_start = int(np.where(time==events[i,2])[0])
                i_end = int(np.where(time==events[i,3])[0])
                # add the first but not the last event to the next, otherwise,
                # flip a coin
                if ((np.random.binomial(1, .5) or i == 0)
                    and i != len(events[:,1])-1
                    ):
                    idealization[i_start:i_end+1] = events[i+1,0]
                    events[i,0] = events[i+1,0]
                    events[i+1,1] += events[i,1] # the event is joined to the
                    # next event so their combined duration needs to be
                    # considered
                else:
                    idealization[i_start:i_end+1] = events[i-1,0]
                    events[i,0] = events[i-1,0]
        return idealization

    @staticmethod
    def extract_events(idealization, time):
        """Summarize an idealized trace as a list of events.

        Args:
            idealization [1D numpy array] - an idealized current trace
            time [1D numpy array] - the corresponding time array
        Return:
            event_list [4D numpy array] - an array containing the amplitude of
                the event, its duration, the time it starts and the time it
                end in its columns"""

        diff = idealization[1:]-idealization[:-1]
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
            event_list[0][0] = idealization[0]
            event_list[0][2] = time[0]
            event_list[0][3] = time[-1]
        else:
            event_list[0][0] = idealization[0]
            event_list[0][2] = time[0]
            event_list[0][3] = time[int(events[0])]
            for i, t in enumerate(events[:-1]):
                event_list[i+1][0] = idealization[int(t)+1]
                event_list[i+1][2] = time[int(events[i])]
                event_list[i+1][3] = time[int(events[i+1])]
            event_list[-1][0] = idealization[int(events[-1])+1]
            event_list[-1][2] = time[(int(events[-1]))]
            event_list[-1][3] = time[-1]
        # get the duration column
        event_list[:,1]=event_list[:,3]-event_list[:,2]
        return event_list

def detect_first_activation(time, signal, threshold):
    """Return the time where a signal first crosses below a threshold."""

    return time[np.argmax(signal<threshold)]

def baseline_correction(time, signal, fs, intervals=None,
                        degree=1, method='poly',select_intvl=False,
                        piezo=None, select_piezo=False, active= False,
                        deviation=0.05):
    """Perform polynomial/offset baseline correction on the given signal.

    Parameters:
        time - 1D array containing times of the measurements in signal
               units of `time_unit`
        signal - time series of measurements
        intervals - interval or list of intervals from which to
                   estimate the baseline (in ms)
        fs - sampling frequency (in Hz)
        time_unit - units of the time vector, 'ms' or 's'
        method - `baseline` can subtract a fitted polynomial of
                 desired degree OR subtract the mean
        degree - if method is 'poly', the degree of the polynomial
    Returns:
        original signal less the fitted baseline"""

    if select_intvl:
        t, s = interval_selection(time, signal, intervals, fs)
    elif select_piezo:
        t, s = piezo_selection(time, piezo, signal, active, deviation)
    else:
        t = time
        s = signal

    if method == 'offset':
        offset = np.mean(s)
        output = signal - offset
    elif method == 'poly':
        coeffs = np.polyfit(t, s, degree)
        baseline = np.zeros_like(time)
        for i in range(degree+1):
            baseline += coeffs[i] * (time**(degree-i))
        output = signal - baseline
    return output
