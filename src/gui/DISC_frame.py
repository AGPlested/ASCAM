import logging

from PySide2 import QtCore
from PySide2.QtWidgets import (
    QLabel,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QToolButton,
    QPushButton,
)

from ..gui import ExportFADialog
from ..utils.widgets import EntryWidget, TableFrame
from ..constants import CURRENT_UNIT_FACTORS
from ..constants import CURRENT_UNIT_FACTORS, ANALYSIS_FRAME_WIDTH

debug_logger = logging.getLogger("ascam.debug")

class DISCFrame(QWidget):
    def __init__(self, main):
        super().__init__()

        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(ANALYSIS_FRAME_WIDTH)

        self.create_widgets()

        # self.main.ep_frame.ep_list.currentItemChanged.connect(self.on_episode_click)

    # @property
    # def current_tab(self):
        # return self.tab_frame.currentWidget()

    def create_widgets(self):
        pass
        # self.tab_frame = IdealizationTabFrame(self)
        # self.layout.addWidget(self.tab_frame)

        # self.calc_button = QPushButton("Calculate idealization")
        # self.calc_button.clicked.connect(self.calculate_click)
        # self.layout.addWidget(self.calc_button)

        # self.events_button = QPushButton("Show Table of Events")
        # self.events_button.clicked.connect(self.create_event_frame)
        # self.layout.addWidget(self.events_button)

        # self.hist_button = QPushButton("Show Dwell Time Histogram")
        # self.hist_button.clicked.connect(self.create_histogram_frame)
        # self.layout.addWidget(self.hist_button)

        # self.export_events_button = QPushButton("Export Table of Events")
        # self.export_events_button.clicked.connect(self.export_events)
        # self.layout.addWidget(self.export_events_button)

        # self.export_idealization_button = QPushButton("Export Idealization")
        # self.export_idealization_button.clicked.connect(self.export_idealization)
        # self.layout.addWidget(self.export_idealization_button)

        # self.close_button = QPushButton("Close Tab")
        # self.close_button.clicked.connect(self.close_tab)
        # self.layout.addWidget(self.close_button)
        # self.layout.addStretch()

    # def on_episode_click(self, item, *args):
        # self.idealize_episode()

    # def close_tab(self):
        # if self.tab_frame.count() > 2:
        #     self.tab_frame.removeTab(self.tab_frame.currentIndex())
        # else:
        #     self.close_frame()

    def close_frame(self):
        # self.main.ep_frame.ep_list.currentItemChanged.disconnect(self.on_episode_click)
        self.main.disc_frame = None
        self.main.plot_frame.update_plots()
        self.close()

    # def create_histogram_frame(self):
        # self.current_tab.create_histogram_frame()

    # def create_event_frame(self):
        # self.current_tab.create_event_frame()

    # def export_events(self):
        # self.get_params()
        # self.current_tab.idealization_cache.get_events()
        # filename = QFileDialog.getSaveFileName(
        #     self, dir=self.main.filename[:-4] + "_events.csv", filter="*.csv"
        # )[0]
        # self.current_tab.idealization_cache.export_events(
        #     filename, self.current_tab.time_unit, self.current_tab.trace_unit
        # )

    # def export_idealization(self):
        # self.get_params()
        # self.idealize_series()
        # ExportIdealizationDialog(self.main, self.current_tab.idealization_cache)
        # # filename = QFileDialog.getSaveFileName(
        # #     self, dir=self.main.filename[:-4] + "_idealization.csv", filter="*.csv"
        # # )[0]
        # # self.current_tab.idealization_cache.export_idealization(
        # #     filename,
        # #     self.current_tab.time_unit,
        # #     self.current_tab.trace_unit,
        # # )

    # def get_params(self):
        # return self.current_tab.get_params()

    # def idealization(self, n_episode=None):
        # if self.current_tab.idealization_cache is not None:
        #     return self.current_tab.idealization_cache.idealization(n_episode)
        # return None

    # def time(self, n_episode=None):
        # return self.current_tab.idealization_cache.time(n_episode)

    # def calculate_click(self):
        # self.get_params()
        # self.idealize_episode()
        # self.main.plot_frame.update_episode()

    # def idealize_episode(self):
        # self.current_tab.idealization_cache.idealize_episode()

    # def idealize_series(self):
        # self.current_tab.idealization_cache.idealize_series()

    # def track_cursor(self, y_pos):
        # """Track the position of the mouse cursor over the plot and if mouse 1
        # is pressed adjust the nearest threshold/amplitude line by dragging the
        # cursor."""

        # amps, thetas = self.get_params()[:2]
        # if thetas.size > 0:
        #     tc_diff = np.min(np.abs(thetas - y_pos))
        # else:
        #     tc_diff = np.inf
        # if amps.size > 0:
        #     amp_diff = np.min(np.abs(amps - y_pos))
        # else:
        #     amp_diff = np.inf

        # y_pos *= CURRENT_UNIT_FACTORS[self.current_tab.trace_unit]
        # if self.current_tab.neg_check.isChecked():
        #     y_pos *= -1
        # if tc_diff < amp_diff and self.current_tab.show_threshold_check.isChecked():
        #     new_str = update_number_in_string(
        #         y_pos, self.current_tab.threshold_entry.toPlainText()
        #     )
        #     self.current_tab.threshold_entry.setPlainText(new_str)
        #     self.current_tab.auto_thresholds.setChecked(False)
        # elif self.current_tab.show_amp_check.isChecked():
        #     new_str = update_number_in_string(
        #         y_pos, self.current_tab.amp_entry.toPlainText()
        #     )
        #     self.current_tab.amp_entry.setPlainText(new_str)
        # self.calculate_click()
