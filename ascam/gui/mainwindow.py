import logging
import os

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
        QDockWidget,
    QGridLayout,
    QWidget,
    QMainWindow,
    QFileDialog,
    QAction,
    QSizePolicy,
)

from ascam.gui import (
    ExportFileDialog,
    OpenFileDialog,
    FilterFrame,
    BaselineFrame,
    PlotFrame,
    EpisodeFrame,
    IdealizationFrame,
    FirstActivationFrame,
)
from ascam.utils import parse_filename
from ascam.core import Recording
from ascam.constants import TEST_FILE_NAME


ana_logger = logging.getLogger("ascam.analysis")
debug_logger = logging.getLogger("ascam.debug")


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        debug_logger.debug("MainWindow initializing")

        self.setWindowTitle("cuteSCAM")
        # self.setGeometry(0,0,800,600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.central_layout = QGridLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self.data = Recording()

        self.create_menu()

        self.create_widgets()

    def create_menu(self):
        debug_logger.debug("MainWindow creating menus")
        self.file_menu = self.menuBar().addMenu("File")
        self.file_menu.addAction("Open File", self.open_file)
        # self.file_menu.addAction("Save", self.save_to_file)
        self.file_menu.addAction("Export Series", lambda: ExportFileDialog(self))
        # self.file_menu.addAction(
        #     "Export First Activation"
        # )  # , lambda: ExportFADialog())
        self.file_menu.addSeparator()
        self.file_menu.addAction("Quit", self.close)

        self.processing_menu = self.menuBar().addMenu("Processing")
        self.processing_menu.addAction(
            "Baseline Correction", lambda: BaselineFrame(self)
        )
        self.processing_menu.addAction("Filter", lambda: FilterFrame(self))

        self.analysis_menu = self.menuBar().addMenu("Analysis")
        self.analysis_menu.addAction("Idealize", self.launch_idealization)
        self.analysis_menu.addAction("First Activation", self.launch_fa_analysis)

        self.plot_menu = self.menuBar().addMenu("Plots")
        self.show_piezo = QAction("Show Piezo Voltage", self.plot_menu, checkable=True)
        self.plot_menu.addAction(self.show_piezo)
        self.show_command = QAction(
            "Show Command Voltage", self.plot_menu, checkable=True
        )
        self.plot_menu.addAction(self.show_command)

        # self.histogram_menu = self.menuBar().addMenu("Histogram")

    def create_widgets(self):
        self.ep_frame = EpisodeFrame(self)
        self.central_layout.addWidget(self.ep_frame, 1, 3)

        self.plot_frame = PlotFrame(self)
        self.show_piezo.triggered.connect(self.plot_frame.toggle_piezo)
        self.show_command.triggered.connect(self.plot_frame.toggle_command)
        self.central_layout.addWidget(self.plot_frame, 1, 2)

    def open_file(self):
        self.filename = QFileDialog.getOpenFileName(self)[0]
        debug_logger.debug(f'filename is {self.filename}')
        _, _, _, filename_short = parse_filename(self.filename)
        OpenFileDialog(self, filename_short)

    def save_to_file(self):
        filename = QFileDialog.getSaveFileName(
            self, dir=self.filename[:-3] + "pkl", filter="*.pkl"
        )[0]
        self.data.save_to_pickle(filename)

    def launch_idealization(self):
        self.tc_frame = IdealizationFrame(self)
        # self.tc_frame.show()
        # dock_widget = QDockWidget(self)
        # dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        # dock_widget.setWidget(self.tc_frame)
        # self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)
        self.central_layout.addWidget(self.tc_frame, 1, 1)
        self.central_widget.adjustSize()

    def launch_fa_analysis(self):
        self.fa_frame = FirstActivationFrame(self)
        self.fa_frame.show()
        self.central_layout.addWidget(self.fa_frame, 2, 2)

    def test_mode(self):
        path = os.path.split(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0])[0]  # data is in project root, ie 2 above this file
        path = os.path.join(path, 'data')
        self.filename = os.path.join(path, TEST_FILE_NAME)
        self.data = Recording.from_file(self.filename)
        self.ep_frame.ep_list.populate()
        self.ep_frame.setFocus()
        self.data.baseline_correction(
            method="Polynomial",
            degree=1,
            intervals=None,
            selection="Piezo",
            deviation=0.05,
            active=False,
        )
        self.data.gauss_filter_series(1000)
        self.ep_frame.update_combo_box()
        self.plot_frame.plot_all()
        self.launch_idealization()
        self.tc_frame.tab_frame.currentWidget().amp_entry.setText("0, -.8, -1.2, -1.6")
