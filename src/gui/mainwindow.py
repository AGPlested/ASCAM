import logging
import os

from PySide2.QtWidgets import (
    QGridLayout,
    QWidget,
    QMainWindow,
    QFileDialog,
    QAction,
    QSizePolicy,
)

from ..gui import (
    ExportDialog,
    OpenFileDialog,
    FilterFrame,
    BaselineFrame,
    PlotFrame,
    EpisodeFrame,
    IdealizationFrame,
    FirstActivationFrame,
)
from ..utils import parse_filename, clear_qt_layout
from ..core import Recording
from ..constants import TEST_FILE_NAME


ana_logger = logging.getLogger("ascam.analysis")
debug_logger = logging.getLogger("ascam.debug")


class MainWindow(QMainWindow):
    def __init__(self, screen_resolution, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        debug_logger.debug("MainWindow initializing")

        self.screen_resolution = screen_resolution

        self.setWindowTitle("cuteSCAM")
        # self.setGeometry(0,0,800,600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.central_layout = QGridLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # Placeholders
        self.fa_frame = None  # FirstActivationFrame.
        self.id_frame = None  # IdealizationFrame
        self.filename = None

        self.data = Recording()

        self.create_menu()

        self.create_widgets()

    def create_menu(self):
        debug_logger.debug("MainWindow creating menus")
        self.file_menu = self.menuBar().addMenu("File")
        self.file_menu.addAction("Open File", self.open_file)
        self.file_menu.addAction("Save Session", self.save_to_file)
        self.file_menu.addAction("Export Data", lambda: ExportDialog(self))
        self.file_menu.addSeparator()
        self.file_menu.addAction("Quit", self.close)

        self.processing_menu = self.menuBar().addMenu("Processing")
        self.processing_menu.addAction(
            "Baseline Correction", lambda: BaselineFrame(self)
        )
        self.processing_menu.addAction("Filter", lambda: FilterFrame(self))

        self.analysis_menu = self.menuBar().addMenu("Analysis")
        self.analysis_menu.addAction("Idealize", self.launch_threshold_crossing)
        self.analysis_menu.addAction("DISC", self.launch_DISC)
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
        self.central_layout.addWidget(self.plot_frame, 1, 2)

    def open_file(self):
        clear_qt_layout(self.central_layout)
        self.create_widgets()
        self.filename = QFileDialog.getOpenFileName(self)[0]
        if self.filename:
            self.close_other_frames()
            debug_logger.debug(f"filename is {self.filename}")
            _, _, _, filename_short = parse_filename(self.filename)
            OpenFileDialog(self, filename=filename_short)

    def save_to_file(self):
        filename = QFileDialog.getSaveFileName(
            self, dir=self.filename[:-3] + "pkl", filter="*.pkl"
        )[0]
        if filename.strip():  # strip to avoid whitespace filenames
            self.data.save_to_pickle(filename)
        else:
            debug_logger.debug("Not saving to pickle - no filename given.")

    def launch_threshold_crossing(self):
        debug_logger.debug("launching threshold crossing idealization")
        if self.id_frame is None:
            self.close_other_frames()
            self.id_frame = IdealizationFrame(self, "TC")
            self.central_layout.addWidget(self.id_frame, 1, 1)
        else:
            debug_logger.debug("IdealizationFrame already exists, adding TC tab.")
            self.id_frame.tab_frame.add_tab(idealization_method="TC")

    def launch_DISC(self):
        debug_logger.debug("launching DISC idealization")
        if self.id_frame is None:
            self.close_other_frames()
            self.id_frame = IdealizationFrame(self, "DISC")
            self.central_layout.addWidget(self.id_frame, 1, 1)
        else:
            debug_logger.debug("IdealizationFrame already exists, adding DISC tab.")
            self.id_frame.tab_frame.add_tab(idealization_method="DISC")

    def launch_fa_analysis(self):
        self.close_other_frames()
        self.fa_frame = FirstActivationFrame(self)
        self.central_layout.addWidget(self.fa_frame, 1, 1)

    def close_other_frames(self):
        if self.fa_frame is not None:
            self.fa_frame.clean_up_and_close()
        if self.id_frame is not None:
            self.id_frame.close_frame()

    def load_example_data(self):
        path = os.path.split(
            os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
        )[
            0
        ]  # data is in project root, ie 2 above this file
        path = os.path.join(path, "data")
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
        self.launch_DISC()
