import logging

# pylint: disable=E0611
from PySide2.QtWidgets import (
    QDialog,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QCheckBox,
    QFormLayout,
)

from ascam.utils import clear_qt_layout


debug_logger = logging.getLogger("ascam.debug")


class FilterFrame(QDialog):
    def __init__(self, main):
        super().__init__()
        self.setWindowTitle("Filter")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.filter_options = ["Gaußian", "Chung-Kennedy"]

        self.create_widgets()
        self.exec_()

    def create_widgets(self):
        row_one = QHBoxLayout()
        method_label = QLabel("Method")
        method_box = QComboBox()
        method_box.addItems(self.filter_options)
        method_box.currentIndexChanged.connect(self.choose_filter_method)
        row_one.addWidget(method_label)
        row_one.addWidget(method_box)

        row_two = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_clicked)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        row_two.addWidget(ok_button)
        row_two.addWidget(cancel_button)

        self.layout.addLayout(row_one)
        self.choose_filter_method(0)
        self.layout.addLayout(row_two)

        self.selection_layout = None

    def choose_filter_method(self, index):
        try:
            debug_logger.debug("deleting selection widgets")
            clear_qt_layout(self.selection_layout)
        except AttributeError:
            pass
        if self.filter_options[index] == "Gaußian":
            self.selection_layout = QHBoxLayout()
            debug_logger.debug("Creating gaussian input widgets")
            self.freq_label = QLabel("Frequency [Hz]")
            self.selection_layout.addWidget(self.freq_label)
            self.freq_entry = QLineEdit("1000")
            self.selection_layout.addWidget(self.freq_entry)
        else:
            debug_logger.debug("creating CK-filter input widgets")
            self.selection_layout = QFormLayout()
            self.width_entry = QLineEdit()
            self.selection_layout.addRow("Predictor Widths", self.width_entry)
            self.exponent_entry = QLineEdit()
            self.selection_layout.addRow("Weight Exponent", self.exponent_entry)
            self.window_entry = QLineEdit()
            self.selection_layout.addRow("Weight Window", self.window_entry)
            self.forward_entry = QLineEdit()
            self.selection_layout.addRow("Forward Pi", self.forward_entry)
            self.backward_entry = QLineEdit()
            self.selection_layout.addRow("Backward Pi", self.backward_entry)
        self.layout.insertLayout(1, self.selection_layout)
        # TODO sizing after switching back and forth
        # self.resize(self.sizeHint())

    def ok_clicked(self):
        # TODO collect information from widgets and pass to parent
        self.close()


class BaselineFrame(QDialog):
    def __init__(self, main):
        super().__init__()
        self.setWindowTitle("Baseline Correction")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.method_options = ["Polynomial", "Offset"]
        self.selection_options = ["Piezo", "Intervals"]

        self.create_widgets()
        self.exec_()

    def create_widgets(self):
        row_one = QHBoxLayout()
        method_label = QLabel("Method")
        method_box = QComboBox()
        method_box.addItems(self.method_options)
        method_box.currentIndexChanged.connect(self.choose_correction_method)
        row_one.addWidget(method_label)
        row_one.addWidget(method_box)

        row_tow = QHBoxLayout()
        selection_label = QLabel("Selection")
        selection_box = QComboBox()
        selection_box.addItems(self.selection_options)
        selection_box.currentIndexChanged.connect(self.choose_selection_method)
        row_tow.addWidget(selection_label)
        row_tow.addWidget(selection_box)

        row_three = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_clicked)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        row_three.addWidget(ok_button)
        row_three.addWidget(cancel_button)

        self.layout.addLayout(row_one)
        self.choose_correction_method(0)
        self.layout.addLayout(row_tow)
        self.choose_selection_method(0)
        self.layout.addLayout(row_three)

        self.method_layout = None
        self.selection_layout = None

    def choose_correction_method(self, index):
        if self.method_options[index] == "Polynomial":
            self.selection_layout = QHBoxLayout()
            debug_logger.debug("Creating polynomial input widgets")
            self.degree_label = QLabel("Degree")
            self.selection_layout.addWidget(self.degree_label)
            self.degree_entry = QLineEdit("1")
            self.selection_layout.addWidget(self.degree_entry)
            self.layout.insertLayout(1, self.selection_layout)
        else:
            debug_logger.debug("Destroying polynomial input widgets")
            try:
                clear_qt_layout(self.selection_layout)
            except AttributeError:
                pass

    def choose_selection_method(self, index):
        try:
            debug_logger.debug("deleting selection widgets")
            clear_qt_layout(self.method_layout)
        except AttributeError:
            pass
        self.method_layout = QHBoxLayout()
        if self.selection_options[index] == "Piezo":
            debug_logger.debug("creating piezo selection widgets")
            self.active_checkbox = QCheckBox("Active/Inactive")
            self.method_layout.addWidget(self.active_checkbox)
            self.deviation_label = QLabel("Deviation")
            self.method_layout.addWidget(self.deviation_label)
            self.deviation_entry = QLineEdit("0.05")
            self.method_layout.addWidget(self.deviation_entry)
        else:
            debug_logger.debug("creating interval widgets")
            self.include_checkbox = QCheckBox("Include/Exclude")
            self.method_layout.addWidget(self.include_checkbox)
            self.interval_label = QLabel("Intervals")
            self.method_layout.addWidget(self.interval_label)
            self.interval_entry = QLineEdit("")
            self.method_layout.addWidget(self.interval_entry)
        self.layout.insertLayout(3, self.method_layout)

    def ok_clicked(self):
        # TODO collect information from widgets and pass to parent
        self.close()
