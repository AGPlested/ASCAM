import logging

from PySide2.QtWidgets import (
    QFileDialog,
    QAction,
    QMenu,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QToolButton,
    QPushButton,
)

from .threshold_crossing_frame import ThresholdCrossingFrame
from .DISC_frame import DISCFrame
from .io_widgets import ExportIdealizationDialog
from ..constants import ANALYSIS_FRAME_WIDTH

debug_logger = logging.getLogger("ascam.debug")


class IdealizationFrame(QWidget):
    def __init__(self, main, idealization_method="TC"):
        super().__init__()

        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(ANALYSIS_FRAME_WIDTH)

        self.main.plot_frame.tc_tracking = False

        self.create_widgets(idealization_method)

        self.main.ep_frame.ep_list.currentItemChanged.connect(self.on_episode_click)

    @property
    def current_tab(self):
        return self.tab_frame.currentWidget()

    def create_widgets(self, idealization_method):
        self.tab_frame = IdealizationTabFrame(self, self.main,
                                              idealization_method)
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
        self.current_tab.on_episode_click(item, *args)

    def close_tab(self):
        if self.tab_frame.count() > 1:
            self.tab_frame.removeTab(self.tab_frame.currentIndex())
        else:
            self.close_frame()

    def close_frame(self):
        self.main.ep_frame.ep_list.currentItemChanged.disconnect(self.on_episode_click)
        self.main.plot_frame.tc_tracking = False
        self.main.tc_frame = None
        self.main.disc_frame = None
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
        try:
            return self.current_tab.idealization_cache.idealization(n_episode)
        except AttributeError as e:
            if "no attribute 'idealization_cache'" in str(e):
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
    def __init__(self, parent, main, idealization_method):
        super().__init__()
        # Parent is the IdealizationFrame.
        self.parent = parent
        self.main = main

        if idealization_method == "TC":
            self.tabs = [ThresholdCrossingFrame(
                parent=self,
                main=self.main,)]
        elif idealization_method == "DISC":
            self.tabs = [DISCFrame(self, self.main)]
        self.addTab(self.tabs[0], "1")

        self.new_tab_button = QToolButton()
        self.new_tab_button.setText("+")
        self.new_tab_button.clicked.connect(self.select_new_tab_type)
        self.setCornerWidget(self.new_tab_button)

        self.setTabsClosable(True)
        self.tabBar().tabCloseRequested.connect(self.removeTab)

        self.currentChanged.connect(self.switch_tab)

    def select_new_tab_type(self):
        menu = QMenu(self)
        add_tc_tab = QAction("Add TC Tab", self)
        add_tc_tab.triggered.connect(lambda: self.add_tab(idealization_method="TC"))
        menu.addAction(add_tc_tab)
        add_disc_tab = QAction("Add DISC Tab", self)
        menu.addAction(add_disc_tab)
        add_disc_tab.triggered.connect(lambda: self.add_tab(idealization_method="DISC"))

        # Show the context menu at the position of the add tab button
        menu.exec_(self.new_tab_button.mapToGlobal(self.new_tab_button.rect().bottomRight()))

    def add_tab(self, idealization_method="TC"):
        title = str(self.count()+1)
        debug_logger.debug(f"adding new {idealization_method} tab with number {title}")
        if idealization_method == "TC":
            tab = ThresholdCrossingFrame(self, self.main)
        elif idealization_method == "DISC":
            tab = DISCFrame(self, self.main)
        else:
            raise ValueError("Unknown idealization method.")
        self.tabs.append(tab)
        ind = self.insertTab(self.count(), tab, title)
        self.setCurrentIndex(ind)

    def switch_tab(self):
        self.parent.idealize_episode()

