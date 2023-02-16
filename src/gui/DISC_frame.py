import logging

import numpy as np
from PySide2 import QtCore
from PySide2.QtGui import QDoubleValidator
from PySide2.QtWidgets import (
    QFrame,
    QApplication,
    QCheckBox,
    QLineEdit,
    QToolButton,
    QLabel,
    QWidget,
    QRadioButton,
    QLineEdit,
    QPushButton,
    QVBoxLayout
)

from ..utils import string_to_array, array_to_string, update_number_in_string
from ..constants import TIME_UNIT_FACTORS, CURRENT_UNIT_FACTORS
from ..core import IdealizationCache
from ..utils.widgets import EntryWidget, VerticalContainerWidget
from PySide2.QtGui import QIntValidator

#import QFrame from pyside2

# import QDoubleValidator from pyside2

debug_logger = logging.getLogger("ascam.debug")


class DISCFrame(VerticalContainerWidget):
    def __init__(self, parent, main):
        super().__init__(parent, main)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.calculate_click()
        else:
            super().keyPressEvent(event)

    def create_widgets(self):
        # self.bic_method_selector = QRadioButton("BIC implmentation")
        # self.layout.addWidget(self.bic_method_selector)

        # add a label "BIC implmentation"
        self.bic_method_label = QLabel("BIC implmentation")
        self.add_row(self.bic_method_label)
        # add two buttons
        self.button1 = QPushButton("approx")
        self.button2 = QPushButton("full")
        # make the buttons checkable
        self.button1.setCheckable(True)
        self.button2.setCheckable(True)
        # check button 1
        self.button1.setChecked(True)
        self.add_row(self.button1, self.button2, spacing=0,
                     contents_margins=(0, 0, 0, 0))
        # checking one button unchecks the other
        self.button1.clicked.connect(
                lambda: self.button2.setChecked(not self.button1.isChecked()))
        self.button2.clicked.connect(
                lambda: self.button1.setChecked(not self.button2.isChecked()))

        self.divseg_frame = DivSegFrame(self, self.main)
        self.add_row(self.divseg_frame)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.add_row(separator)
        self.ac_frame = ACFrame(self, self.main)
        self.add_row(self.ac_frame)
        self.add_row(separator)
        self.viterbi_frame = ViterbiFrame(self, self.main)
        self.add_row(self.viterbi_frame)

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
                if "'IdealizationTab' object has no attribute 'idealization_cache'" in str(
                    e
                ) or "object has no attribute " in str(
                    e
                ):
                    pass
                else:
                    raise AttributeError(e)
            self.idealization_cache = IdealizationCache(
                self.parent.parent.main.data, amps, thresholds, resolution, intrp_factor
            )
        return amps, thresholds, resolution, intrp_factor

    def calculate_click(self):
        self.get_params()
        self.idealize_episode()
        self.parent.parent.main.plot_frame.update_episode()

    def on_episode_click(self, *args):
        self.idealize_episode()

    def idealize_episode(self):
        pass
        # self.idealization_cache.idealize_episode()

    def idealize_series(self):
        pass
        # self.idealization_cache.idealize_series()

    def close_frame(self):
        self.main.disc_frame = None
        self.main.plot_frame.update_plots()
        self.close()

class DivSegFrame(EntryWidget):
    def __init__(self, parent, main):
        super().__init__(parent, main)

    def create_widgets(self):
        # create a numerical input for the alpha value
        self.alpha_label = QLabel("t-test α=")
        self.alpha_entry = QLineEdit("0.001")
        self.alpha_entry.setValidator(QDoubleValidator())
        self.add_row(self.alpha_label, self.alpha_entry)

        # add a button to run change point detection
        self.change_point_button = QPushButton("Detect Change Points")
        self.change_point_button.clicked.connect(self.detect_change_points)
        self.layout.addWidget(self.change_point_button)

        # create an integer input for the minimum segment length
        self.min_seg_label = QLabel("min lengeth segments:")
        self.min_seg_entry = QLineEdit("3")
        self.min_seg_entry.setValidator(QIntValidator())
        self.add_row(self.min_seg_label, self.min_seg_entry)

        # add a button to run divisive segmentation
        self.div_seg_button = QPushButton("Divisive Segment")
        self.div_seg_button.clicked.connect(self.div_seg)
        self.layout.addWidget(self.div_seg_button)

    def detect_change_points(self):
        raise NotImplementedError

    def div_seg(self):
        raise NotImplementedError

class ACFrame(EntryWidget):
    def __init__(self, parent, main):
        super().__init__(parent, main)

    def create_widgets(self):
        self.ac_label = QLabel("Agglomerative clustering")
        self.layout.addWidget(self.ac_label)

        # add entry for min cluster size
        self.min_cluster_label = QLabel("min cluster size:")
        self.min_cluster_entry = QLineEdit("3")
        self.min_cluster_entry.setValidator(QIntValidator())
        self.add_row(self.min_cluster_label, self.min_cluster_entry)

        # add entry for desired number of clusters
        self.num_states_label = QLabel("max num states:")
        self.num_states_entry = QLineEdit("3")
        self.num_states_entry.setValidator(QIntValidator())
        self.add_row(self.num_states_label, self.num_states_entry)

        # add a button to run agglomerative clustering
        self.ac_button = QPushButton("Run Agglomerative Clustering")
        self.ac_button.clicked.connect(self.run_ac)
        self.layout.addWidget(self.ac_button)

    def run_ac(self):
        raise NotImplementedError

class ViterbiFrame(EntryWidget):
    def __init__(self, parent, main):
        super().__init__(parent, main)

    def create_widgets(self):
        self.viterbi_label = QLabel("viterbi")
        self.layout.addWidget(self.viterbi_label)

        # add a button to run viterbi
        self.viterbi_button = QPushButton("Run Viterbi")
        self.viterbi_button.clicked.connect(self.run_viterbi)
        self.layout.addWidget(self.viterbi_button)

    def run_viterbi(self):
        raise NotImplementedError
