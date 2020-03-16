import logging

import numpy as np
from PySide2.QtCore import QAbstractTableModel, Qt
from PySide2.QtWidgets import (
    QComboBox,
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


debug_logger = logging.getLogger("ascam.debug")


class IdealizationFrame(QWidget):
    def __init__(self, main):
        super().__init__()

        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(250)

        self.main.plot_frame.tc_tracking = True

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

        self.close_button = QPushButton("Close Tab")
        self.close_button.clicked.connect(self.close_tab)
        self.layout.addWidget(self.close_button)
        self.layout.addStretch()

    def close_tab(self):
        if self.tab_frame.count() > 2:
            self.tab_frame.removeTab(self.tab_frame.currentIndex())
        else:
            self.main.plot_frame.tc_tracking = False
            self.close()

    def create_event_frame(self):
        self.current_tab.event_table = self.create_table()
        self.event_table_frame = EventTableFrame(self, self.current_tab.event_table)

    def create_table(self):
        # self.idealize_series()
        self.get_params()
        events = self.current_tab.idealization_cache.get_events(
                current_unit=self.current_tab.trace_unit.currentText(),
                time_unit=self.current_tab.time_unit.currentText()
                )
        return EventTableModel(
            events,
            self.current_tab.trace_unit.currentText(),
            self.current_tab.time_unit.currentText()
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
            update_number_in_string(y_pos, self.current_tab.threshold_entry)
            self.current_tab.auto_thresholds.setChecked(False)
        elif self.current_tab.show_amp_check.isChecked():
            update_number_in_string(y_pos, self.current_tab.amp_entry)
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
        row_one = QHBoxLayout()
        amp_label = QLabel("Amplitudes")
        row_one.addWidget(amp_label)
        
        self.show_amp_check = QCheckBox("Show")
        self.show_amp_check.setChecked(True)
        row_one.addWidget(self.show_amp_check)
        self.layout.addLayout(row_one)
        
        self.neg_check = QCheckBox("Treat as negative")
        self.layout.addWidget(self.neg_check)
        
        row_two = QHBoxLayout()
        self.amp_entry = QLineEdit()  # TODO add button to toggle plot interaction
        row_two.addWidget(self.amp_entry)
        self.trace_unit = QComboBox()
        self.trace_unit.addItems(list(CURRENT_UNIT_FACTORS.keys()))
        self.trace_unit.setCurrentIndex(1)
        row_two.addWidget(self.trace_unit)
        self.drag_amp_toggle = QToolButton()
        self.drag_amp_toggle.setCheckable(True)
        self.drag_amp_toggle.setText("M")
        self.drag_amp_toggle.setChecked(self.parent.parent.main.plot_frame.tc_tracking)
        self.drag_amp_toggle.clicked.connect(self.toggle_drag_params)
        row_two.addWidget(self.drag_amp_toggle)
        self.layout.addLayout(row_two)

        row_three = QHBoxLayout()
        threshold_label = QLabel("Thresholds")
        row_three.addWidget(threshold_label)
        self.show_threshold_check = QCheckBox("Show")
        row_three.addWidget(self.show_threshold_check)
        
        
        #row_three.addWidget(self.auto_thresholds)
        self.layout.addLayout(row_three)

        self.auto_thresholds = QCheckBox("Auto-Generate")
        self.auto_thresholds.stateChanged.connect(self.toggle_auto_theta)
        self.layout.addWidget(self.auto_thresholds)

        self.threshold_entry = QLineEdit()
        self.layout.addWidget(self.threshold_entry)

        row_four = QHBoxLayout()
        res_label = QLabel("Resolution")
        row_four.addWidget(res_label)
        
        self.use_res = QCheckBox("Apply")
        self.use_res.stateChanged.connect(self.toggle_resolution)
        row_four.addWidget(self.use_res)
        self.layout.addLayout(row_four)

        row_five = QHBoxLayout()
        self.res_entry = QLineEdit()
        row_five.addWidget(self.res_entry)
        
        self.time_unit = QComboBox()
        self.time_unit.addItems(list(TIME_UNIT_FACTORS.keys()))
        self.time_unit.setCurrentIndex(1)
        row_five.addWidget(self.time_unit)
        self.layout.addLayout(row_five)

        row_six = QHBoxLayout()
        intrp_label = QLabel("Interpolation")
        row_six.addWidget(intrp_label)
        self.interpolate = QCheckBox("Apply")
        self.interpolate.stateChanged.connect(self.toggle_interpolation)
        row_six.addWidget(self.interpolate)
        self.layout.addLayout(row_six)

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
        amps = string_to_array(self.amp_entry.text())
        thresholds = string_to_array(self.threshold_entry.text())
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

        trace_factor = CURRENT_UNIT_FACTORS[
            self.trace_unit.currentText()
        ]
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

        if not self.check_params_unchanged(amps, thresholds, resolution, intrp_factor):
            debug_logger.debug(f'creating new idealization cache for\n'
                               f'amp = {amps} \n'
                               f'thresholds = {thresholds}\n'
                               f'resolution = {res_string}\n'
                               f'interpolation = {intrp_string}')
            self.idealization_cache = IdealizationCache(self.parent.parent.main.data,
                            amps, thresholds, resolution, intrp_factor)
        return amps, thresholds, resolution, intrp_factor

    def check_params_unchanged(self,amp, theta,res, intrp):
        try:
            if set(amp) != set(self.idealization_cache.amplitudes):
                debug_logger.debug('amps have changed')
                return False
            if set(theta) != set(self.idealization_cache.thresholds):
                debug_logger.debug('thresholds have changed')
                return False
            if res != self.idealization_cache.resolution:
                debug_logger.debug('resolution has changed')
                return False
            if intrp != self.idealization_cache.interpolation_factor:
                debug_logger.debug('interpolation factor has changed')
                return False
            return True
        except AttributeError:
            return False


class EventTableFrame(QDialog):
    def __init__(self, parent, table_view):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Events")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        height =800
        width = 500
        self.setGeometry(parent.x()+width/4, parent.y()+height/3, width, height)

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
