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

from ..utils import clear_qt_layout, string_to_list
from ..utils.widgets import VerticalContainerWidget


debug_logger = logging.getLogger("ascam.debug")


class FilterFrame(QDialog):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.setWindowTitle("Filter")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.filter_options = ["Gaussian", "Chung-Kennedy"]

        self.create_widgets()
        self.freq_entry.setFocus()
        self.exec_()

    def create_widgets(self):
        row_one = QHBoxLayout()
        method_label = QLabel("Method")
        self.method_box = QComboBox()
        self.method_box.addItems(self.filter_options)
        self.method_box.currentIndexChanged.connect(self.choose_filter_method)
        row_one.addWidget(method_label)
        row_one.addWidget(self.method_box)

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

    def choose_filter_method(self, index):
        try:
            debug_logger.debug("deleting selection widgets")
            clear_qt_layout(self.selection_layout)
        except AttributeError:
            pass
        self.resize(self.sizeHint())
        if self.filter_options[index] == "Gaussian":
            debug_logger.debug("Creating gaussian input widgets")
            self.selection_layout = QFormLayout()
            self.freq_entry = QLineEdit("1000")
            self.selection_layout.addRow("Frequency [Hz]", self.freq_entry)
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
        self.resize(self.sizeHint())  # both resizes are necessary

    def ok_clicked(self):
        filter_method = self.filter_options[self.method_box.currentIndex()]
        if filter_method == "Gaussian":
            self.main.data.gauss_filter_series(float(self.freq_entry.text()))
        elif filter_method == "Chung-Kennedy":
            self.main.data.CK_filter_series(
                window_lengths=[int(x) for x in self.window_entry.text().split()],
                weight_exponent=int(self.exponent_entry.text()),
                weight_window=int(self.window_entry.text()),
                apriori_f_weights=[int(x) for x in self.forward_entry.text().split()],
                apriori_b_weights=[int(x) for x in self.backward_entry.text().split()],
            )
        self.main.plot_frame.plot_all()
        self.main.ep_frame.update_combo_box()
        self.close()


class BaselineFrame(QDialog):
    def __init__(self, main):
        super().__init__()
        self.setWindowTitle("Baseline Correction")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(BaselineWidget(main, self))

        self.exec_()


class BaselineWidget(VerticalContainerWidget):
    def __init__(self, main, dialog):
        self.method_options = ["Polynomial", "Offset"]
        self.selection_options = ["Piezo", "Intervals"]

        super().__init__(main)

        self.main = main
        self.dialog = dialog

    def create_widgets(self):
        method_label = QLabel("Method")
        self.method_box = QComboBox()
        self.method_box.addItems(self.method_options)
        self.method_box.currentIndexChanged.connect(self.choose_correction_method)
        self.add_row(method_label, self.method_box)
        self.choose_correction_method(0)

        selection_label = QLabel("Selection")
        self.selection_box = QComboBox()
        self.selection_box.addItems(self.selection_options)
        self.selection_box.currentIndexChanged.connect(self.choose_selection_method)
        self.add_row(selection_label, self.selection_box)
        self.choose_selection_method(0)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_clicked)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel_clicked)
        self.add_row(ok_button, cancel_button)


    def choose_correction_method(self, index):
        if self.method_options[index] == "Polynomial":
            self.selection_layout = QFormLayout()
            debug_logger.debug("Creating polynomial input widgets")
            self.degree_entry = QLineEdit("1")
            self.selection_layout.addRow("Degree", self.degree_entry)
            self.layout.insertLayout(1, self.selection_layout)
        else:
            debug_logger.debug("Destroying polynomial input widgets")
            clear_qt_layout(self.selection_layout)

    def choose_selection_method(self, index):
        try:
            debug_logger.debug("deleting selection widgets")
            clear_qt_layout(self.method_layout)
        except AttributeError:
            pass
        self.method_layout = QHBoxLayout()
        if self.selection_options[index] == "Piezo":
            debug_logger.debug("creating piezo selection widgets")
            self.active_checkbox = QCheckBox("Active")
            self.active_checkbox.setToolTip("If checked the baseline correction will be based"
                    " on the times where the Piezo voltage is within a factor `deviation` of its"
                    " maximum value. If unchecked it will be based on the times where the voltage"
                    " is within a factor `deviation` of its minimum value.")
            self.active_checkbox.setChecked(False)
            self.method_layout.addWidget(self.active_checkbox)
            self.deviation_label = QLabel("Deviation")
            self.method_layout.addWidget(self.deviation_label)
            self.deviation_entry = QLineEdit("0.05")
            self.method_layout.addWidget(self.deviation_entry)
        else:
            debug_logger.debug("creating interval widgets")
            self.interval_label = QLabel("Intervals")
            self.method_layout.addWidget(self.interval_label)
            self.interval_entry = QLineEdit("")
            self.interval_entry.setToolTip("Enter second intervals surround by square brackets"
                    " and seperated by commans, eg: '[0, 10], [70, 100]'")
            self.method_layout.addWidget(self.interval_entry)
        # insert the newly created layout in the 3rd or 4th row
        # depending on whether there is an entry field for the correction method
        pos = 3 + int(self.method_box.currentText() == "Polynomial") 
        self.layout.insertLayout(pos, self.method_layout)

    def ok_clicked(self):
        method = self.method_options[self.method_box.currentIndex()]
        degree = int(self.degree_entry.text())
        selection = self.selection_options[self.selection_box.currentIndex()]
        if selection == "Piezo":
            intervals = None
            deviation = float(self.deviation_entry.text())
            active = self.active_checkbox.isChecked()
        elif selection == "Intervals":
            active = None
            deviation = None
            intervals = string_to_list(self.interval_entry.text())

        self.main.data.baseline_correction(
            method=method,
            degree=degree,
            intervals=intervals,
            selection=selection,
            deviation=deviation,
            active=active,
        )
        self.main.ep_frame.update_combo_box()
        self.main.plot_frame.plot_all()
        self.dialog.close()
        self.close()

    def cancel_clicked(self):
        self.dialog.close()
        self.close()
