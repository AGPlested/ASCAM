import logging

import numpy as np
import pyqtgraph as pg
from PySide2.QtWidgets import (
    QFileDialog,
    QDialog,
    QGridLayout,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QToolButton,
    QPushButton,
)

from .threshold_crossing_frame import ThresholdCrossingFrame
from .io_widgets import ExportIdealizationDialog
from ..utils.widgets import HistogramViewBox
from ..constants import ANALYSIS_FRAME_WIDTH

debug_logger = logging.getLogger("ascam.debug")


class IdealizationFrame(QWidget):
    def __init__(self, main):
        super().__init__()

        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(ANALYSIS_FRAME_WIDTH)

        self.main.plot_frame.tc_tracking = False

        self.create_widgets()

        self.main.ep_frame.ep_list.currentItemChanged.connect(self.on_episode_click)

    @property
    def current_tab(self):
        return self.tab_frame.currentWidget()

    def create_widgets(self):
        self.tab_frame = IdealizationTabFrame(self)
        self.layout.addWidget(self.tab_frame)

        self.events_button = QPushButton("Show Table of Events")
        self.events_button.clicked.connect(self.create_event_frame)
        self.layout.addWidget(self.events_button)

        self.hist_button = QPushButton("Show Dwell Time Histogram")
        self.hist_button.clicked.connect(self.create_histogram_frame)
        self.layout.addWidget(self.hist_button)

        self.export_events_button = QPushButton("Export Table of Events")
        self.export_events_button.clicked.connect(self.export_events)
        self.layout.addWidget(self.export_events_button)

        self.export_idealization_button = QPushButton("Export Idealization")
        self.export_idealization_button.clicked.connect(self.export_idealization)
        self.layout.addWidget(self.export_idealization_button)

        self.close_button = QPushButton("Close Tab")
        self.close_button.clicked.connect(self.close_tab)
        self.layout.addWidget(self.close_button)
        self.layout.addStretch()

    def on_episode_click(self, item, *args):
        self.idealize_episode()

    def close_tab(self):
        if self.tab_frame.count() > 1:
            self.tab_frame.removeTab(self.tab_frame.currentIndex())
        else:
            self.close_frame()

    def close_frame(self):
        self.main.ep_frame.ep_list.currentItemChanged.disconnect(self.on_episode_click)
        self.main.plot_frame.tc_tracking = False
        self.main.tc_frame = None
        self.main.plot_frame.update_plots()
        self.close()

    def create_histogram_frame(self):
        self.current_tab.create_histogram_frame()

    def create_event_frame(self):
        self.current_tab.create_event_frame()

    def export_events(self):
        self.get_params()
        self.current_tab.idealization_cache.get_events()
        filename = QFileDialog.getSaveFileName(
            self, dir=self.main.filename[:-4] + "_events.csv", filter="*.csv"
        )[0]
        self.current_tab.idealization_cache.export_events(
            filename, self.current_tab.time_unit, self.current_tab.trace_unit
        )

    def export_idealization(self):
        self.get_params()
        self.current_tab.idealize_series()
        ExportIdealizationDialog(self.main, self.current_tab.idealization_cache)

    def get_params(self):
        return self.current_tab.get_params()

    def idealization(self, n_episode=None):
        if self.current_tab.idealization_cache is not None:
            return self.current_tab.idealization_cache.idealization(n_episode)
        return None

    def time(self, n_episode=None):
        return self.current_tab.idealization_cache.time(n_episode)

    def idealize_episode(self):
        self.current_tab.idealization_cache.idealize_episode()

    def idealize_series(self):
        self.current_tab.idealization_cache.idealize_series()

    def track_cursor(self, y_pos):
        self.current_tab.track_cursor(y_pos)


class IdealizationTabFrame(QTabWidget):
    def __init__(self, parent):
        super().__init__()
        # Parent is the IdealizationFrame.
        self.parent = parent

        self.tabs = [ThresholdCrossingFrame(self)]
        self.addTab(self.tabs[0], "1")

        self.new_tab_button = QToolButton()
        self.new_tab_button.setText("+")
        self.new_tab_button.clicked.connect(self.add_tab)
        self.setCornerWidget(self.new_tab_button)

        self.setTabsClosable(True)
        self.tabBar().tabCloseRequested.connect(self.removeTab)

        self.currentChanged.connect(self.switch_tab)

    def add_tab(self):
        title = str(self.count()+1)
        debug_logger.debug(f"adding new tab with number {title}")
        tab = ThresholdCrossingFrame(self)
        self.tabs.append(tab)
        ind = self.insertTab(self.count(), tab, title)
        self.setCurrentIndex(ind)

    def switch_tab(self):
        self.parent.idealize_episode()


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
            debug_logger.debubg(
                f"argument n_bins is being ignoroed because it is incorrect n_bins={n_bins}"
            )
        n_cols = np.round(np.sqrt(len(self.amps)))
        self.histograms = []
        i = j = 0
        for amp in self.amps:
            debug_logger.debug(f"getting hist for {amp}")
            if n_bins is None:
                histogram = Histogram(
                    histogram_frame=self,
                    idealization_cache=self.parent.idealization_cache,
                    amp=amp,
                    log_times=log_times,
                    root_counts=root_counts,
                    time_unit=time_unit,
                )
            else:
                histogram = Histogram(
                    histogram_frame=self,
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
        histogram_frame=None,
        idealization_cache=None,
        amp=None,
        n_bins=None,
        time_unit="ms",
        log_times=True,
        root_counts=True,
        trace_unit="pA",
    ):
        self.histogram_frame = histogram_frame
        self.idealization_cache = idealization_cache
        self.amp = amp
        self.n_bins = n_bins
        self.time_unit = time_unit
        self.log_times = log_times
        self.root_counts = root_counts
        self.trace_unit = trace_unit

        self.widget = self.create_widgets()
        self.row = None
        self.col = None

    def create_widgets(self):
        heights, bins = self.idealization_cache.dwell_time_hist(
            self.amp, self.n_bins, self.time_unit, self.log_times, self.root_counts
        )
        self.n_bins = len(bins) - 1
        hist_viewbox = HistogramViewBox(
            histogram=self,
            histogram_frame=self.histogram_frame,
            amp=self.amp,
            n_bins=self.n_bins,
            time_unit=self.time_unit,
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
            histogram_frame=self.histogram_frame,
            amp=self.amp,
            n_bins=self.n_bins,
            time_unit=self.time_unit,
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
        self.histogram_frame.layout.addWidget(self.widget, self.row, self.col)
