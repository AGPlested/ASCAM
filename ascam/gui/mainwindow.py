import logging

# pylint: disable=E0611
from PySide2.QtWidgets import QGridLayout, QWidget, QMainWindow, QFileDialog, QAction

# from ascam.gui import ExportFADialog
# from ascam.gui import ExportFileDialog
from ascam.gui import FilterFrame
from ascam.gui import BaselineFrame
from ascam.gui import PlotFrame
from ascam.gui import EpisodeFrame
from ascam.gui import IdealizationFrame
from ascam.gui import FirstActivationFrame

from ascam.core.recording import Recording

from ascam.constants import TEST_FILE_NAME


ana_logger = logging.getLogger("ascam.analysis")
debug_logger = logging.getLogger("ascam.debug")


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        debug_logger.debug("MainWindow initializing")

        self.setWindowTitle("cuteSCAM")

        self.central_layout = QGridLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self.data = Recording()

        self.create_widgets()

        self.create_menu()

    def create_menu(self):
        debug_logger.debug("MainWindow creating menus")
        self.file_menu = self.menuBar().addMenu("File")
        self.file_menu.addAction("Open File", self.open_file)
        self.file_menu.addAction("Save", self.save_to_file)
        self.file_menu.addAction("Export")  # , lambda: ExportFileDialog())
        self.file_menu.addAction("Export Idealization", self.export_idealization)
        self.file_menu.addAction("Export Events", self.export_events)
        self.file_menu.addAction(
            "Export First Activation"
        )  # , lambda: ExportFADialog())
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
        show_piezo = QAction("Show Piezo Voltage", self.plot_menu, checkable=True)
        show_piezo.triggered.connect(self.plot_frame.toggle_piezo)
        self.plot_menu.addAction(show_piezo)
        show_piezo.setChecked(True)
        show_command = QAction("Show Command Voltage", self.plot_menu, checkable=True)
        show_command.triggered.connect(self.plot_frame.toggle_command)
        self.plot_menu.addAction(show_command)

        # self.histogram_menu = self.menuBar().addMenu("Histogram")

    def create_widgets(self):
        self.plot_frame = PlotFrame(self)
        self.central_layout.addWidget(self.plot_frame, 1, 2)

        self.ep_frame = EpisodeFrame(self)
        self.central_layout.addWidget(self.ep_frame, 1, 3)

    def open_file(self):
        self.filename = QFileDialog.getOpenFileName(self)[0]
        self.data = Recording.from_file(self.filename)
        self.ep_frame.populate()
        self.ep_frame.setFocus()
        self.plot_frame.plot_all()

    def save_to_file(self):
        filename = QFileDialog.getSaveFileName(
            self, dir=self.filename[:-3] + "pkl", filter="*.pkl"
        )[0]
        self.data.save_to_pickle(filename)

    def export_events(self):
        pass

    def export_idealization(self):
        pass

    def launch_idealization(self):
        self.tc_frame = IdealizationFrame(self)
        self.tc_frame.show()
        self.central_layout.addWidget(self.tc_frame, 1, 1)

    def launch_fa_analysis(self):
        self.fa_frame = FirstActivationFrame(self)
        self.fa_frame.show()
        self.central_layout.addWidget(self.fa_frame, 2, 2)

    def test_mode(self):
        self.data = Recording.from_file(TEST_FILE_NAME)
        self.ep_frame.populate()
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
        self.plot_frame.plot_all()
        self.launch_idealization()
        self.tc_frame.tab_frame.currentWidget().amp_entry.setText("0, -.8, -1.2, -1.6")
