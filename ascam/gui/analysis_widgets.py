import logging

import numpy as np
import pyqtgraph as pg
from PySide2.QtCore import QAbstractTableModel, Qt
from PySide2.QtWidgets import (
        QSizePolicy,
    QComboBox,
    QFileDialog,
    QDialog,
    QTableView,
    QGridLayout,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QToolButton,
    QTabBar,
    QPushButton,
    QLabel,
)

from ascam.utils import string_to_array, array_to_string, update_number_in_string
from ascam.constants import TIME_UNIT_FACTORS, CURRENT_UNIT_FACTORS
from ascam.core import IdealizationCache
from ascam.utils.widgets import TextEdit, CustomViewBox

debug_logger = logging.getLogger("ascam.debug")


class IdealizationFrame(QWidget):
    def __init__(self, main):
        super().__init__()

        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(250)

        self.main.plot_frame.tc_tracking = False

        self.create_widgets()

    @property
    def current_tab(self):
        return self.tab_frame.currentWidget()

    def create_widgets(self):
        self.tab_frame = IdealizationTabFrame(self)
        self.layout.addWidget(self.tab_frame)

        self.calc_button = QPushButton("Calculate idealization")
        self.calc_button.clicked.connect(self.calculate_click)
        self.layout.addWidget(self.calc_button)

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

    def close_tab(self):
        if self.tab_frame.count() > 2:
            self.tab_frame.removeTab(self.tab_frame.currentIndex())
        else:
            self.main.plot_frame.tc_tracking = False
            del self.main.tc_frame
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
            filename,
            self.current_tab.time_unit.currentText(),
            self.current_tab.trace_unit.currentText(),
        )

    def export_idealization(self):
        self.get_params()
        self.idealize_series()
        filename = QFileDialog.getSaveFileName(
            self, dir=self.main.filename[:-4] + "_idealization.csv", filter="*.csv"
        )[0]
        self.current_tab.idealization_cache.export_idealization(
            filename,
            self.current_tab.time_unit.currentText(),
            self.current_tab.trace_unit.currentText(),
        )

    def get_params(self):
        return self.current_tab.get_params()

    def idealization(self, n_episode=None):
        return self.current_tab.idealization_cache.idealization(n_episode)

    def time(self, n_episode=None):
        return self.current_tab.idealization_cache.time(n_episode)

    def calculate_click(self):
        self.get_params()
        self.idealize_episode()
        self.main.plot_frame.update_episode()

    def idealize_episode(self):
        self.current_tab.idealization_cache.idealize_episode()

    def idealize_series(self):
        self.current_tab.idealization_cache.idealize_series()

    def track_cursor(self, y_pos):
        """Track the position of the mouse cursor over the plot and if mouse 1
        is pressed adjust the nearest threshold/amplitude line by dragging the
        cursor."""

        amps, thetas = self.get_params()[:2]
        if thetas.size > 0:
            tc_diff = np.min(np.abs(thetas - y_pos))
        else:
            tc_diff = np.inf
        if amps.size > 0:
            amp_diff = np.min(np.abs(amps - y_pos))
        else:
            amp_diff = np.inf

        y_pos *= CURRENT_UNIT_FACTORS[self.current_tab.trace_unit.currentText()]
        if self.current_tab.neg_check.isChecked():
            y_pos *= -1
        if tc_diff < amp_diff and self.current_tab.show_threshold_check.isChecked():
            new_str = update_number_in_string(y_pos, self.current_tab.threshold_entry.toPlainText())
            self.current_tab.threshold_entry.setPlainText(new_str)
            self.current_tab.auto_thresholds.setChecked(False)
        elif self.current_tab.show_amp_check.isChecked():
            new_str = update_number_in_string(y_pos, self.current_tab.amp_entry.toPlainText())
            self.current_tab.amp_entry.setPlainText(new_str)
        self.calculate_click()


class IdealizationTabFrame(QTabWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.tabs = [IdealizationTab(self)]
        self.addTab(self.tabs[0], "1")

        self.insertTab(1, QWidget(), "")
        self.new_button = QToolButton()
        self.new_button.setText("+")
        self.new_button.clicked.connect(self.add_tab)
        self.tabBar().setTabButton(1, QTabBar.RightSide, self.new_button)

        self.setTabsClosable(True)
        self.tabBar().tabCloseRequested.connect(self.removeTab)

        self.currentChanged.connect(self.switch_tab)

    def add_tab(self):
        title = str(self.count())
        debug_logger.debug(f"adding new tab with number {title}")
        tab = IdealizationTab(self)
        self.tabs.append(tab)
        ind = self.insertTab(self.count() - 1, tab, title)
        self.setCurrentIndex(ind)

    def switch_tab(self):
        self.parent.idealize_episode()


class IdealizationTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.create_widgets()

    def create_widgets(self):
        row = QHBoxLayout()
        amp_label = QLabel("Amplitudes")
        row.addWidget(amp_label)
        self.show_amp_check = QCheckBox("Show")
        self.show_amp_check.setChecked(True)
        row.addWidget(self.show_amp_check)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        self.neg_check = QCheckBox("Treat as negative")
        row.addWidget(self.neg_check)
        self.trace_unit = QComboBox()
        self.trace_unit.addItems(list(CURRENT_UNIT_FACTORS.keys()))
        self.trace_unit.setCurrentIndex(1)
        row.addWidget(self.trace_unit)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        self.drag_amp_toggle = QToolButton()
        self.drag_amp_toggle.setCheckable(True)
        self.drag_amp_toggle.setText("Drag lines to change parameters")
        self.drag_amp_toggle.setChecked(self.parent.parent.main.plot_frame.tc_tracking)
        self.drag_amp_toggle.clicked.connect(self.toggle_drag_params)
        row.addWidget(self.drag_amp_toggle)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        self.amp_entry = TextEdit()
        row.addWidget(self.amp_entry)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        threshold_label = QLabel("Thresholds")
        row.addWidget(threshold_label)
        self.show_threshold_check = QCheckBox("Show")
        row.addWidget(self.show_threshold_check)
        self.layout.addLayout(row)

        self.auto_thresholds = QCheckBox("Auto-Generate")
        self.auto_thresholds.stateChanged.connect(self.toggle_auto_theta)
        self.layout.addWidget(self.auto_thresholds)

        self.threshold_entry = TextEdit()
        self.layout.addWidget(self.threshold_entry)

        row = QHBoxLayout()
        res_label = QLabel("Resolution")
        row.addWidget(res_label)

        self.use_res = QCheckBox("Apply")
        self.use_res.stateChanged.connect(self.toggle_resolution)
        row.addWidget(self.use_res)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        self.res_entry = QLineEdit()
        row.addWidget(self.res_entry)

        self.time_unit = QComboBox()
        self.time_unit.addItems(list(TIME_UNIT_FACTORS.keys()))
        self.time_unit.setCurrentIndex(1)
        row.addWidget(self.time_unit)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        intrp_label = QLabel("Interpolation")
        row.addWidget(intrp_label)
        self.interpolate = QCheckBox("Apply")
        self.interpolate.stateChanged.connect(self.toggle_interpolation)
        row.addWidget(self.interpolate)
        self.layout.addLayout(row)

        self.intrp_entry = QLineEdit()
        self.layout.addWidget(self.intrp_entry)

    def toggle_drag_params(self, checked):
        self.parent.parent.main.plot_frame.tc_tracking = checked

    def toggle_interpolation(self, state):
        if not state:
            self.intrp_entry.setEnabled(False)
        else:
            self.intrp_entry.setEnabled(True)

    def toggle_resolution(self, state):
        if not state:
            self.res_entry.setEnabled(False)
        else:
            self.res_entry.setEnabled(True)

    def toggle_auto_theta(self, state):
        # apparently state==2 if the box is checked and 0
        # if it is not
        if state:
            self.threshold_entry.setEnabled(False)
        else:
            self.threshold_entry.setEnabled(True)

    def get_params(self):
        amps = string_to_array(self.amp_entry.toPlainText())
        thresholds = string_to_array(self.threshold_entry.toPlainText())
        res_string = self.res_entry.text()
        intrp_string = self.intrp_entry.text()

        if self.auto_thresholds.isChecked() or (
            thresholds is None or thresholds.size != amps.size - 1
        ):
            thresholds = (amps[1:] + amps[:-1]) / 2
            self.threshold_entry.setText(array_to_string(thresholds))
            self.auto_thresholds.setChecked(True)
            self.threshold_entry.setEnabled(False)

        if self.neg_check.isChecked():
            amps *= -1
            thresholds *= -1

        trace_factor = CURRENT_UNIT_FACTORS[self.trace_unit.currentText()]
        amps /= trace_factor
        thresholds /= trace_factor
        time_factor = TIME_UNIT_FACTORS[self.time_unit.currentText()]

        if res_string.strip() and self.use_res.isChecked():
            resolution = float(res_string)
            resolution /= time_factor
        else:
            resolution = None

        if intrp_string.strip() and self.interpolate.isChecked():
            intrp_factor = int(intrp_string)
        else:
            intrp_factor = 1

        if self.check_params_changed(amps, thresholds, resolution, intrp_factor):
            debug_logger.debug(
                f"creating new idealization cache for\n"
                f"amp = {amps} \n"
                f"thresholds = {thresholds}\n"
                f"resolution = {res_string}\n"
                f"interpolation = {intrp_string}"
            )
            self.idealization_cache = IdealizationCache(
                self.parent.parent.main.data, amps, thresholds, resolution, intrp_factor
            )
        return amps, thresholds, resolution, intrp_factor

    def check_params_changed(self, amp, theta, res, intrp):
        changed = True
        try:
            if set(amp) != set(self.idealization_cache.amplitudes):
                debug_logger.debug("amps have changed")
            elif set(theta) != set(self.idealization_cache.thresholds):
                debug_logger.debug("thresholds have changed")
            elif res != self.idealization_cache.resolution:
                debug_logger.debug("resolution has changed")
            elif intrp != self.idealization_cache.interpolation_factor:
                debug_logger.debug("interpolation factor has changed")
            else:
                changed = False
        except AttributeError:
            pass
        if changed:
            try:
                debug_logger.debug('changing name of old histogram frame')
                name = self.hist_frame.windowTitle()
                self.event_table_frame.setWindowTitle(f"outdated - {name}")
            except AttributeError:
                pass
            try:
                debug_logger.debug('changing name of old event table')
                name = self.event_table_frame.windowTitle()
                self.event_table_frame.setWindowTitle(f"outdated - {name}")
            except AttributeError:
                pass
        return changed

    def create_histogram_frame(self):
        params = self.get_params()
        self.hist_frame = HistogramFrame(self, amps=params[0])
        self.hist_frame.setWindowTitle(
            f"Amp={params[0]}; Thresh={params[1]}; "
            f"Res={params[2]}; Intrp={params[3]}"
        )

    def create_event_frame(self):
        self.event_table = self.create_table()
        self.event_table_frame = EventTableFrame(self, self.event_table)
        params = self.get_params()
        self.event_table_frame.setWindowTitle(
            f"Amp={params[0]}; Thresh={params[1]}; "
            f"Res={params[2]}; Intrp={params[3]}"
        )

    def create_table(self):
        self.get_params()
        events = self.idealization_cache.get_events(
            current_unit=self.trace_unit.currentText(),
            time_unit=self.time_unit.currentText(),
        )
        return EventTableModel(
            events,
            self.trace_unit.currentText(),
            self.time_unit.currentText(),
        )


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

    def create_histogram(self, amp, n_bins=None, time_unit='ms', log_times=True,
                         root_counts=True):
        heights, bins = self.parent.idealization_cache.dwell_time_hist(amp,
                n_bins, time_unit, log_times=log_times, root_counts=root_counts)
        hist_viewbox = CustomViewBox(self, amp=amp, n_bins=len(bins)-1, time_unit=time_unit)
        x_label = f"Log10 Dwell Time [log({time_unit})]" if log_times else f"Dwell Time [{time_unit}]"
        y_label = f"Sqrt(Counts)" if root_counts else "Counts"
        hist_widget = pg.PlotWidget(viewBox=hist_viewbox, title=f'{amp}', labels={'left': (y_label), 'bottom': (x_label)})
        hist_widget.setBackground("w")
        hist_widget.plot(bins, heights, stepMode=True, pen=pg.mkPen(width=2), fillLevel=0, fillOutline=True, brush=(0,0,255,150))
        return hist_widget, len(bins)-1

    def create_histograms(self, log_times=True, root_counts=True, time_unit='ms'):
        n_cols = np.round(np.sqrt(len(self.amps)))
        self.hist_widgets = {}
        i = j =0
        for amp in self.amps:
            debug_logger.debug(f'getting hist for {amp}')
            hist_widget, n_bins = self.create_histogram(
                    amp=amp,
                    log_times=log_times,
                    root_counts=root_counts,
                    time_unit=time_unit)
            self.hist_widgets[amp] = (hist_widget, i, j, n_bins)
            self.layout.addWidget(hist_widget, i, j)
            j += 1
            if j > n_cols:
                i += 1
                j = 0

    def update_hist(self, amp, n_bins=None, time_unit='ms', log_times=True,
                    root_counts=True):
        heights, bins = self.parent.idealization_cache.dwell_time_hist(amp,
                n_bins, time_unit, log_times=log_times, root_counts=root_counts)
        widget, row, col, n_bins = self.hist_widgets[amp]
        widget.deleteLater()
        hist_viewbox = CustomViewBox(self, amp=amp, n_bins=len(bins)-1,
                time_unit=time_unit)
        x_label = f"Log10 Dwell Time [log({time_unit})]" if log_times else f"Dwell Time [{time_unit}]"
        y_label = f"Sqrt(Counts)" if root_counts else "Counts"
        hist_widget = pg.PlotWidget(viewBox=hist_viewbox, title=f'{amp}', labels={'left': (y_label), 'bottom': (x_label)})
        hist_widget.setBackground("w")
        hist_widget.plot(bins, heights, stepMode=True, pen=pg.mkPen(width=2), fillLevel=0, fillOutline=True, brush=(0,0,255,150))
        self.layout.addWidget(hist_widget, row, col)
        self.hist_widgets[amp] = (hist_widget, row, col, len(bins)-1)


class EventTableFrame(QDialog):
    def __init__(self, parent, table_view):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        height = 800
        width = 500
        self.setGeometry(parent.x() + width / 4, parent.y() + height / 3, width, height)

        self.event_table = QTableView()
        self.event_table.setModel(table_view)

        self.layout.addWidget(self.event_table)
        self.setModal(False)
        self.show()


class EventTableModel(QAbstractTableModel):
    def __init__(self, data, current_unit, time_unit):
        super().__init__()
        self._data = data
        self._data[:, 0]
        self._data[:, 1:]

        self._header = [
            "Episode #",
            f"Amplitude [{current_unit}]",
            f"Duration [{time_unit}]",
            f"t_start [{time_unit}]",
            f"t_stop [{time_unit}]",
        ]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            if index.row() == 0:
                return self._header[index.column()]
            return self._data[index.row() - 1][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])


class FirstActivationFrame(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.create_widgets()

    def create_widgets(self):
        threshold_button = QPushButton("Set threshold")
        threshold_entry = QLineEdit()
        self.layout.addWidget(threshold_button, 1, 1)
        self.layout.addWidget(threshold_entry, 1, 2)

        mark_button = QPushButton("Mark events manually")
        jump_checkbox = QCheckBox("Click jumps to next episode:")
        self.layout.addWidget(mark_button, 2, 1)
        self.layout.addWidget(jump_checkbox, 2, 2)

        finish_button = QPushButton("Finish")
        cancel_button = QPushButton("Cancel")
        self.layout.addWidget(finish_button, 3, 1)
        self.layout.addWidget(cancel_button, 3, 2)