import logging

from PySide2 import QtCore
from PySide2.QtGui import QDoubleValidator
from PySide2.QtWidgets import (
    QFrame,
    QLineEdit,
    QLabel,
    QLineEdit,
    QPushButton,
)

from ..utils import string_to_array, array_to_string
from ..constants import DEFAULT_DISC_ALPHA, TIME_UNIT_FACTORS, AMPERE_UNIT_FACTORS
from ..core import IdealizationCache
from ..utils.widgets import EntryWidget, VerticalContainerWidget
from PySide2.QtGui import QIntValidator


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
        self.approx_BIC_button = QPushButton("approx")
        self.full_BIC_button = QPushButton("full")
        # make the buttons checkable
        self.approx_BIC_button.setCheckable(True)
        self.full_BIC_button.setCheckable(True)
        # check button 1
        self.approx_BIC_button.setChecked(True)
        self.add_row(self.approx_BIC_button, self.full_BIC_button, spacing=0,
                     contents_margins=(0, 0, 0, 0))
        # checking one button unchecks the other
        self.approx_BIC_button.clicked.connect(
                lambda: self.full_BIC_button.setChecked(not self.approx_BIC_button.isChecked()))
        self.full_BIC_button.clicked.connect(
                lambda: self.approx_BIC_button.setChecked(not self.full_BIC_button.isChecked()))

        self.divseg_frame = DivSegFrame(self, self.main)
        self.add_row(self.divseg_frame)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.add_row(separator)
        self.ac_frame = ACFrame(self, self.main)
        self.add_row(self.ac_frame)
        self.add_row(separator)

        # add button that can be toggled for using piezo selection or not
        self.use_piezo_button = QPushButton("Use piezo selection")
        self.use_piezo_button.setCheckable(True)
        self.use_piezo_button.setChecked(True)
        # add text entry for deviation from max piezo voltage
        self.piezo_deviation_entry = QLineEdit()
        self.piezo_deviation_entry.setValidator(QDoubleValidator())
        self.piezo_deviation_entry.setText("0.05")
        # add label
        self.piezo_deviation_label = QLabel("Deviation:")
        self.add_row(self.use_piezo_button)
        self.add_row(self.piezo_deviation_label, self.piezo_deviation_entry)
        # if data has no piezo, disable piezo selection
        if not self.main.data.has_piezo:
            self.use_piezo_button.setEnabled(False)
            self.piezo_deviation_entry.setEnabled(False)
            self.piezo_deviation_label.setEnabled(False)
            debug_logger.info("No piezo data found, disabling piezo selection")

        # add run disc button
        self.run_disc_button = QPushButton("Run DISC")
        self.add_row(self.run_disc_button)
        self.run_disc_button.clicked.connect(self.calculate_click)

        # self.viterbi_frame = ViterbiFrame(self, self.main)
        # self.add_row(self.viterbi_frame)

    def get_params(self):
        BIC_method = "approx" if self.approx_BIC_button.isChecked() else "full"
        alpha = float(self.divseg_frame.alpha_entry.text())
        min_seg_length = int(self.divseg_frame.min_seg_entry.text())
        min_cluster_size = int(self.ac_frame.min_cluster_entry.text())
        if self.main.data.has_piezo:
            piezo_selection = self.use_piezo_button.isChecked()
            deviation = float(self.piezo_deviation_entry.text())
        else:
            piezo_selection = False
            deviation = None

        try:
            changed = self.idealization_cache.check_params_changed(
                alpha=alpha,
                min_seg_length=min_seg_length,
                min_cluster_size=min_cluster_size,
                piezo_selection=piezo_selection,
                deviation=deviation)
        except AttributeError as e:
            if ("'DISCFrame' object has no attribute 'idealization_cache'" in str(e)):
                changed = True
            else:
                raise AttributeError(e)
        if changed:
            debug_logger.debug(
                f"creating new idealization cache for\n"
                f"alpha: {alpha}\n"
                f"min_seg_length: {min_seg_length}\n"
                f"min_cluster_size: {min_cluster_size}\n"
                f"piezo_selection: {piezo_selection}\n"
                f"deviation: {deviation}"
            )
            try:
                self.idealization_cache.clear_idealization()
            except AttributeError as e:
                if ("'DISCFrame' object has no attribute 'idealization_cache'" in str(e)):
                    pass
                else:
                    raise AttributeError(e)
            self.idealization_cache = IdealizationCache(
                self.main.data, method="DISC", alpha=alpha,
                BIC_method=BIC_method,
                min_seg_length=min_seg_length,
                min_cluster_size=min_cluster_size,
                piezo_selection=piezo_selection, deviation=deviation
            )
        return alpha, min_seg_length, min_cluster_size, piezo_selection, deviation

    def calculate_click(self):
        self.get_params()
        self.idealize_episode()
        self.main.plot_frame.update_episode()

    def on_episode_click(self, *_):
        self.idealize_episode()

    def idealize_episode(self):
        self.idealization_cache.idealize_episode()

    def idealize_series(self):
        self.idealization_cache.idealize_series()

    def close_frame(self):
        if self.main is not None:
            self.main.disc_frame = None
            if self.main.plot_frame is not None:
                self.main.plot_frame.update_plots()
        self.close()

class DivSegFrame(EntryWidget):
    def __init__(self, parent, main):
        super().__init__(parent, main)

    def create_widgets(self):
        # create a numerical input for the alpha value
        self.alpha_label = QLabel("t-test α=")
        self.alpha_entry = QLineEdit(str(DEFAULT_DISC_ALPHA))
        self.alpha_entry.setValidator(QDoubleValidator())
        self.add_row(self.alpha_label, self.alpha_entry)

        # # add a button to run change point detection
        # self.change_point_button = QPushButton("Detect Change Points")
        # self.change_point_button.clicked.connect(self.detect_change_points)
        # self.layout.addWidget(self.change_point_button)

        # add and entry for minimum segment length
        self.min_seg_label = QLabel("min segment length:")
        self.min_seg_entry = QLineEdit("3")
        self.min_seg_entry.setValidator(QIntValidator())
        self.add_row(self.min_seg_label, self.min_seg_entry)

        # # add a button to run divisive segmentation
        # self.div_seg_button = QPushButton("Divisive Segmentation")
        # self.div_seg_button.clicked.connect(self.div_seg)
        # self.layout.addWidget(self.div_seg_button)

    # def detect_change_points(self):
    #     raise NotImplementedError

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

        # # add entry for desired number of clusters
        # self.num_states_label = QLabel("max num states:")
        # self.num_states_entry = QLineEdit("3")
        # self.num_states_entry.setValidator(QIntValidator())
        # self.add_row(self.num_states_label, self.num_states_entry)

        # # add a button to run agglomerative clustering
        # self.ac_button = QPushButton("Agglomerative Clustering")
        # self.ac_button.clicked.connect(self.run_ac)
        # self.layout.addWidget(self.ac_button)

    def run_ac(self):
        raise NotImplementedError

# class ViterbiFrame(EntryWidget):
#     def __init__(self, parent, main):
#         super().__init__(parent, main)

#     def create_widgets(self):
#         self.viterbi_label = QLabel("viterbi")
#         self.layout.addWidget(self.viterbi_label)

#         # add a button to run viterbi
#         self.viterbi_button = QPushButton("Run Viterbi")
#         self.viterbi_button.clicked.connect(self.run_viterbi)
#         self.layout.addWidget(self.viterbi_button)

#     def run_viterbi(self):
#         raise NotImplementedError
