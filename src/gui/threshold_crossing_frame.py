import logging

import numpy as np
from PySide2 import QtCore
from PySide2.QtGui import QDoubleValidator
from PySide2.QtWidgets import (
    QApplication,
    QCheckBox,
    QLineEdit,
    QToolButton,
    QPushButton,
    QLabel,
)

from ..utils import string_to_array, array_to_string, update_number_in_string
from ..constants import TIME_UNIT_FACTORS, CURRENT_UNIT_FACTORS
from ..core import IdealizationCache
from ..utils.widgets import TextEdit, EntryWidget, TableFrame

debug_logger = logging.getLogger("ascam.debug")


class ThresholdCrossingFrame(EntryWidget):
    def __init__(self, parent, main):
        # Parent is the IdealizationTabFrame widget.
        super().__init__(parent=parent, main=main)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if QApplication.focusWidget() == self.resolution_entry:
                self.use_resolution.setChecked(True)
            elif QApplication.focusWidget() == self.threshold_entry:
                self.show_threshold_check.setChecked(True)
            elif QApplication.focusWidget() == self.intrp_entry:
                self.interpolate.setChecked(True)
            self.calculate_click()
        else:
            super().keyPressEvent(event)

    def create_widgets(self):
        amp_label = QLabel("Amplitudes")
        self.show_amp_check = QCheckBox("Show")
        self.show_amp_check.setChecked(True)
        self.add_row(amp_label, self.show_amp_check)

        self.neg_check = QToolButton()
        self.neg_check.setText("-1×")
        self.neg_check.setCheckable(True)
        self.add_row(self.neg_check, self.trace_unit_entry)

        self.amp_entry = TextEdit(self)
        self.add_row(self.amp_entry)

        self.drag_amp_toggle = QToolButton()
        self.drag_amp_toggle.setCheckable(True)
        self.drag_amp_toggle.setText("Drag lines to change\n parameters")
        self.drag_amp_toggle.setChecked(self.parent.parent.main.plot_frame.tc_tracking)
        self.drag_amp_toggle.clicked.connect(self.toggle_drag_params)
        self.add_row(self.drag_amp_toggle)

        threshold_label = QLabel("Thresholds")
        self.show_threshold_check = QCheckBox("Show")
        self.add_row(threshold_label, self.show_threshold_check)

        self.auto_thresholds = QCheckBox("Auto-Generate")
        self.auto_thresholds.stateChanged.connect(self.toggle_auto_theta)
        self.add_row(self.auto_thresholds)

        self.threshold_entry = TextEdit(self)
        self.add_row(self.threshold_entry)

        res_label = QLabel("Resolution")
        self.use_resolution = QCheckBox("Apply")
        self.use_resolution.stateChanged.connect(self.toggle_resolution)
        self.add_row(res_label, self.use_resolution)

        self.resolution_entry = QLineEdit(self)
        self.resolution_entry.setValidator(QDoubleValidator())
        self.add_row(self.resolution_entry, self.time_unit_entry)

        intrp_label = QLabel("Interpolation")
        self.interpolate = QCheckBox("Apply")
        self.interpolate.stateChanged.connect(self.toggle_interpolation)
        self.add_row(intrp_label, self.interpolate)

        self.intrp_entry = QLineEdit(self)
        self.intrp_entry.setValidator(QDoubleValidator())
        self.add_row(self.intrp_entry)

        self.calc_button = QPushButton("Apply Threshold Crossing")
        self.calc_button.clicked.connect(self.calculate_click)
        self.layout.addWidget(self.calc_button)

    def calculate_click(self):
        self.get_params()
        self.idealize_episode()
        self.parent.parent.main.plot_frame.update_episode()

    def on_episode_click(self, *_):
        self.idealize_episode()

    def idealize_episode(self):
        self.idealization_cache.idealize_episode()

    def idealize_series(self):
        self.idealization_cache.idealize_series()

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

        y_pos *= CURRENT_UNIT_FACTORS[self.trace_unit]
        if self.neg_check.isChecked():
            y_pos *= -1
        if tc_diff < amp_diff and self.show_threshold_check.isChecked():
            new_str = update_number_in_string(
                y_pos, self.threshold_entry.toPlainText()
            )
            self.threshold_entry.setPlainText(new_str)
            self.auto_thresholds.setChecked(False)
        elif self.show_amp_check.isChecked():
            new_str = update_number_in_string(
                y_pos, self.amp_entry.toPlainText()
            )
            self.amp_entry.setPlainText(new_str)
        self.calculate_click()

    def toggle_drag_params(self, checked):
        self.parent.parent.main.plot_frame.tc_tracking = checked

    def toggle_interpolation(self, state):
        if not state:
            self.intrp_entry.setEnabled(False)
        else:
            self.intrp_entry.setEnabled(True)

    def toggle_resolution(self, state):
        if not state:
            self.resolution_entry.setEnabled(False)
        else:
            self.resolution_entry.setEnabled(True)

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
        res_string = self.resolution_entry.text()
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

        trace_factor = CURRENT_UNIT_FACTORS[self.trace_unit]
        amps /= trace_factor
        thresholds /= trace_factor
        time_factor = TIME_UNIT_FACTORS[self.time_unit]

        if res_string.strip() and self.use_resolution.isChecked():
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
            try:
                self.idealization_cache.clear_idealization()
            except AttributeError as e:
                if "no attribute 'idealization_cache'" in str(e):
                    pass
                else:
                    raise AttributeError(e)
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
        except AttributeError as e:
            if  "no attribute 'idealization_cache'" not in str(e):
                raise AttributeError(e)
        if changed:
            try:
                debug_logger.debug("changing name of old histogram frame")
                name = self.hist_frame.windowTitle()
                self.event_table_frame.setWindowTitle(f"outdated - {name}")
            except AttributeError:
                pass
            try:
                debug_logger.debug("changing name of old event table")
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
        params = self.get_params()
        self.event_table_frame = TableFrame(
            self,
            data=self.idealization_cache.get_events(
                trace_unit=self.trace_unit, time_unit=self.time_unit
            ),
            header=[
                "Episode #",
                f"Amplitude [{self.trace_unit}]",
                f"Duration [{self.time_unit}]",
                f"t_start [{self.time_unit}]",
                f"t_stop [{self.time_unit}]",
            ],
            title=f"Amp={params[0]}; Thresh={params[1]}; Res={params[2]}; Intrp={params[3]}",
            trace_unit=self.trace_unit,
            time_unit=self.time_unit,
        )

