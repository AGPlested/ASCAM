import logging

# from PySide2 import QtCore
from PySide2.QtWidgets import (
    QLabel,
    QWidget,
    QRadioButton,
    QLineEdit,
    QPushButton,
    QVBoxLayout
)

from ..utils.widgets import EntryWidget
from ..constants import ANALYSIS_FRAME_WIDTH

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

    def create_widgets(self):
        self.bic_method_selector = QRadioButton("BIC implmentation")
        self.layout.addWidget(self.bic_method_selector)

        self.divseg_frame = DivSegFrame(self)
        self.layout.addWidget(self.divseg_frame)
        self.ac_frame = ACFrame(self)
        self.layout.addWidget(self.ac_frame)
        self.viterbi_frame = ViterbiFrame(self)
        self.layout.addWidget(self.viterbi_frame)

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
    #     self.idealize_episode()

    def close_frame(self):
        # self.main.ep_frame.ep_list.currentItemChanged.disconnect(self.on_episode_click)
        self.main.disc_frame = None
        self.main.plot_frame.update_plots()
        self.close()

class DivSegFrame(EntryWidget):
    def __init__(self, main):
        self.main = main
        super().__init__(main)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.div_seg_label = QLabel("Divisive segmentation")
        self.layout.addWidget(self.div_seg_label)

        self.div_seg_button = QPushButton("Divide & Segment")
        self.div_seg_button.clicked.connect(self.div_seg)
        self.layout.addWidget(self.div_seg_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_frame)
        self.layout.addWidget(self.close_button)

class ACFrame(EntryWidget):
    def __init__(self, main):
        self.main = main
        super().__init__(main)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.div_seg_label = QLabel("Divisive segmentation")
        self.layout.addWidget(self.div_seg_label)

        self.div_seg_button = QPushButton("Divide & Segment")
        self.div_seg_button.clicked.connect(self.div_seg)
        self.layout.addWidget(self.div_seg_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_frame)
        self.layout.addWidget(self.close_button)

class ViterbiFrame(EntryWidget):
    def __init__(self, main):
        self.main = main
        super().__init__(main)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.div_seg_label = QLabel("Divisive segmentation")
        self.layout.addWidget(self.div_seg_label)

        self.div_seg_button = QPushButton("Divide & Segment")
        self.div_seg_button.clicked.connect(self.div_seg)
        self.layout.addWidget(self.div_seg_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_frame)
        self.layout.addWidget(self.close_button)
