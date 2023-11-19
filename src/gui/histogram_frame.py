import logging

import numpy as np
import pyqtgraph as pg
from PySide2.QtWidgets import QDialog, QGridLayout

from ..utils.widgets import HistogramViewBox

debug_logger = logging.getLogger("ascam.debug")


class HistogramFrame(QDialog):
    def __init__(self, parent, amps):
        super().__init__()
        self.parent = parent
        self.amps = amps
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        height = 800
        width = 1200
        self.setGeometry(parent.x() + width / 4, parent.y() + height / 3, width, height)

        self.create_histograms()
        self.setModal(False)
        self.show()

    def create_histograms(
        self, log_times=True, root_counts=True, time_unit="ms", n_bins=None
    ):
        if n_bins is not None and len(n_bins) != len(self.amps):
            n_bins = None
            debug_logger.debug(
                f"argument n_bins is being ignoroed because it is incorrect n_bins={n_bins}"
            )
        n_cols = np.round(np.sqrt(len(self.amps)))
        self.histograms = []
        i = j = 0
        for amp in self.amps:
            debug_logger.debug(f"getting hist for {amp}")
            if n_bins is None:
                histogram = Histogram(
                    idealization_cache=self.parent.idealization_cache,
                    amp=amp,
                    log_times=log_times,
                    root_counts=root_counts,
                    time_unit=time_unit,
                )
            else:
                histogram = Histogram(
                    idealization_cache=self.parent.idealization_cache,
                    n_bins=n_bins[amp],
                    amp=amp,
                    log_times=log_times,
                    root_counts=root_counts,
                    time_unit=time_unit,
                )
            self.histograms.append(histogram)
            self.layout.addWidget(histogram.widget, i, j)
            histogram.row = i
            histogram.col = j
            j += 1
            if j > n_cols:
                i += 1
                j = 0


class Histogram:
    def __init__(
        self,
        idealization_cache,
        amp=None,
        n_bins=None,
        time_unit="ms",
        log_times=True,
        root_counts=True,
        trace_unit="pA",
    ):
        self.idealization_cache = idealization_cache
        self.amp = amp
        self.n_bins = n_bins
        self.time_unit = time_unit
        self.log_times = log_times
        self.root_counts = root_counts
        self.trace_unit = trace_unit

        self.widget = self.create_widgets()
        self.row = -1
        self.col = -1

    def create_widgets(self):
        heights, bins = self.idealization_cache.dwell_time_hist(
            self.amp, self.n_bins, self.time_unit, self.log_times, self.root_counts
        )
        self.n_bins = len(bins) - 1
        hist_viewbox = HistogramViewBox(
            histogram=self,
            # amp=self.amp,
            # n_bins=self.n_bins,
            # time_unit=self.time_unit,
        )
        x_label = (
            f"Log10 Dwell Time [log({self.time_unit})]"
            if self.log_times
            else f"Dwell Time [{self.time_unit}]"
        )
        y_label = f"Sqrt(Counts)" if self.root_counts else "Counts"
        hist_widget = pg.PlotWidget(
            viewBox=hist_viewbox,
            title=f"{self.amp:.3g}",
            labels={"left": (y_label), "bottom": (x_label)},
        )
        hist_widget.setBackground("w")
        hist_widget.plot(
            bins,
            heights,
            stepMode=True,
            pen=pg.mkPen(width=2),
            fillLevel=0,
            fillOutline=True,
            brush=(0, 0, 255, 150),
        )
        return hist_widget

    def update_hist(self):
        debug_logger.debug(
            f"updating histogram for {self.amp} with n_bins={self.n_bins}, time_unit={self.time_unit}, "
            f"log_times={self.log_times}, root_counts={self.root_counts}"
        )
        heights, bins = self.idealization_cache.dwell_time_hist(
            self.amp, self.n_bins, self.time_unit, self.log_times, self.root_counts
        )
        self.widget.deleteLater()
        hist_viewbox = HistogramViewBox(
            histogram=self,
            # amp=self.amp,
            # n_bins=self.n_bins,
            # time_unit=self.time_unit,
        )
        x_label = (
            f"Log10 Dwell Time [log({self.time_unit})]"
            if self.log_times
            else f"Dwell Time [{self.time_unit}]"
        )
        y_label = f"Sqrt(Counts)" if self.root_counts else "Counts"
        self.widget = pg.PlotWidget(
            viewBox=hist_viewbox,
            title=f"{self.amp:.3g}",
            labels={"left": (y_label), "bottom": (x_label)},
        )
        self.widget.setBackground("w")
        self.widget.plot(
            bins,
            heights,
            stepMode=True,
            pen=pg.mkPen(width=2),
            fillLevel=0,
            fillOutline=True,
            brush=(0, 0, 255, 150),
        )
        # self.layout.addWidget(self.widget, self.row, self.col)
