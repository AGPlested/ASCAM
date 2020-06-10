from PySide2 import QtGui
from PySide2.QtWidgets import (
    QLineEdit,
    QDialog,
    QComboBox,
    QCheckBox,
    QPushButton,
    QListWidget,
    QLabel,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
)


from ..core import Recording
from ..constants import (
    TIME_UNIT_FACTORS,
    CURRENT_UNIT_FACTORS,
    VOLTAGE_UNIT_FACTORS,
)


class ExportFADialog(QDialog):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()

        self.exec_()

    def create_widgets(self):
        self.series_selection = QComboBox()
        self.series_selection.addItems(list(self.main.data.keys()))
        self.series_selection.setCurrentText(self.main.data.current_datakey)
        self.layout.addWidget(self.series_selection)

        self.list_selection = QListWidget()
        self.list_selection.addItems(list(self.main.data.lists.keys()))
        self.list_selection.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.list_selection.setCurrentRow(0)
        self.layout.addWidget(self.list_selection)

        row = QHBoxLayout()
        label = QLabel("Time Unit:")
        row.addWidget(label)
        self.time_unit = QComboBox()
        self.time_unit.addItems(list(TIME_UNIT_FACTORS.keys()))
        self.time_unit.setCurrentIndex(2)
        row.addWidget(self.time_unit)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        label = QLabel("Current Unit:")
        row.addWidget(label)
        self.trace_unit = QComboBox()
        self.trace_unit.addItems(list(CURRENT_UNIT_FACTORS.keys()))
        self.trace_unit.setCurrentIndex(5)
        row.addWidget(self.trace_unit)
        self.layout.addLayout(row)

        row = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_click)
        row.addWidget(save_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        row.addWidget(cancel_button)
        self.layout.addLayout(row)

    def save_click(self):
        filename, filetye = QFileDialog.getSaveFileName(
            self,
            dir=self.main.filename[:-4]+"_first_activation",
            filter="Comma Separated Valued (*.csv)",
        )
        if filename:
            self.main.data.export_first_activation(
                filepath=filename,
                datakey=self.series_selection.currentText(),
                lists_to_save=[
                    item.text() for item in self.list_selection.selectedItems()
                ],
                time_unit=self.time_unit.currentText(),
                trace_unit=self.trace_unit.currentText(),
            )
        self.close()


class OpenFileDialog(QDialog):
    def __init__(self, main, filename):
        super().__init__()
        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(300)

        self.filename = filename
        self.create_widgets()

        self.exec_()

    def create_widgets(self):
        row_one = QHBoxLayout()
        file_button = QLabel("File:")
        row_one.addWidget(file_button)
        self.file_name_label = QLabel(self.filename)
        row_one.addWidget(self.file_name_label)
        self.layout.addLayout(row_one)

        row_two = QHBoxLayout()
        sampling_label = QLabel("Smapling rate [Hz]")
        row_two.addWidget(sampling_label)
        self.sampling_entry = QLineEdit("40000")
        row_two.addWidget(self.sampling_entry)
        self.layout.addLayout(row_two)

        row_three = QHBoxLayout()
        t_unit_label = QLabel("Time unit")
        row_three.addWidget(t_unit_label)
        self.time_unit = QComboBox()
        self.time_unit.addItems(list(TIME_UNIT_FACTORS.keys()))
        self.time_unit.setCurrentIndex(2)
        row_three.addWidget(self.time_unit)
        self.layout.addLayout(row_three)

        row_four = QHBoxLayout()
        t_unit_label = QLabel("Current unit")
        row_four.addWidget(t_unit_label)
        self.trace_unit = QComboBox()
        self.trace_unit.addItems(list(CURRENT_UNIT_FACTORS.keys()))
        self.trace_unit.setCurrentIndex(5)
        row_four.addWidget(self.trace_unit)
        self.layout.addLayout(row_four)

        row_five = QHBoxLayout()
        t_unit_label = QLabel("Piezo unit")
        row_five.addWidget(t_unit_label)
        self.piezo_unit = QComboBox()
        self.piezo_unit.addItems(list(VOLTAGE_UNIT_FACTORS.keys()))
        self.piezo_unit.setCurrentIndex(2)
        row_five.addWidget(self.piezo_unit)
        self.layout.addLayout(row_five)

        row_six = QHBoxLayout()
        t_unit_label = QLabel("Command unit")
        row_six.addWidget(t_unit_label)
        self.command_unit = QComboBox()
        self.command_unit.addItems(list(VOLTAGE_UNIT_FACTORS.keys()))
        self.command_unit.setCurrentIndex(2)
        row_six.addWidget(self.command_unit)
        self.layout.addLayout(row_six)

        row_seven = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_clicked)
        row_seven.addWidget(ok_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        row_seven.addWidget(cancel_button)
        self.layout.addLayout(row_seven)

    def ok_clicked(self):
        self.main.data = Recording.from_file(
            filename=self.main.filename,
            sampling_rate=self.sampling_entry.text(),
            time_input_unit=self.time_unit.currentText(),
            trace_input_unit=self.trace_unit.currentText(),
            piezo_input_unit=self.piezo_unit.currentText(),
            command_input_unit=self.command_unit.currentText(),
        )
        self.main.ep_frame.ep_list.populate()
        self.main.ep_frame.setFocus()
        self.main.plot_frame.plot_all()
        self.main.setWindowTitle(f"cuteSCAM {self.main.filename}")
        self.close()


class ExportFileDialog(QDialog):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()

        self.exec_()

    def create_widgets(self):
        self.series_selection = QComboBox()
        self.series_selection.addItems(list(self.main.data.keys()))
        self.layout.addWidget(self.series_selection)

        row_two = QHBoxLayout()
        self.save_piezo = QCheckBox()
        row_two.addWidget(self.save_piezo)
        self.save_command = QCheckBox()
        row_two.addWidget(self.save_command)
        self.layout.addLayout(row_two)

        self.list_selection = QListWidget()
        self.list_selection.addItems(list(self.main.data.lists.keys()))
        self.list_selection.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.list_selection.setCurrentRow(0)
        self.layout.addWidget(self.list_selection)

        row_four = QHBoxLayout()
        label = QLabel("Time Unit:")
        row_four.addWidget(label)
        self.time_unit_selection = QComboBox()
        self.time_unit_selection.addItems(list(TIME_UNIT_FACTORS.keys()))
        self.time_unit_selection.setCurrentIndex(2)
        self.layout.addLayout(row_four)

        row_five = QHBoxLayout()
        label = QLabel("Current Unit:")
        row_five.addWidget(label)
        self.trace_unit_selection = QComboBox()
        self.trace_unit_selection.addItems(list(CURRENT_UNIT_FACTORS.keys()))
        self.trace_unit_selection.setCurrentIndex(4)
        self.layout.addLayout(row_five)

        row_six = QHBoxLayout()
        label = QLabel("Piezo Unit:")
        row_six.addWidget(label)
        self.piezo_unit_selection = QComboBox()
        self.piezo_unit_selection.addItems(list(VOLTAGE_UNIT_FACTORS.keys()))
        self.piezo_unit_selection.setCurrentIndex(2)
        self.layout.addLayout(row_six)

        row_seven = QHBoxLayout()
        label = QLabel("Command Unit:")
        row_seven.addWidget(label)
        self.command_unit_selection = QComboBox()
        self.command_unit_selection.addItems(list(VOLTAGE_UNIT_FACTORS.keys()))
        self.command_unit_selection.setCurrentIndex(2)
        self.layout.addLayout(row_seven)

        row_eight = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_click)
        row_eight.addWidget(save_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        row_eight.addWidget(cancel_button)
        self.layout.addLayout(row_eight)

    def save_click(self):
        filename, filetye = QFileDialog.getSaveFileName(
            self,
            dir=self.main.filename[:-4],
            filter="Axograph (*.axgd);; Matlab (*.mat)",
        )
        if filename:
            if "Matlab" in filetye:
                self.main.data.export_matlab(
                    filepath=filename,
                    datakey=self.series_selection.currentText(),
                    lists_to_save=[
                        item.text() for item in self.list_selection.selectedItems()
                    ],
                    save_piezo=self.save_piezo.isChecked(),
                    save_command=self.save_command.isChecked(),
                    time_unit=self.time_unit.text(),
                    trace_unit=self.trace_unit.text(),
                    piezo_unit=self.piezo_unit.text(),
                    command_unit=self.command_unit.text(),
                )
            elif "Axograph" in filetye:
                self.main.data.export_matlab(
                    filepath=filename,
                    datakey=self.series_selection.currentText(),
                    lists_to_save=[
                        item.text() for item in self.list_selection.selectedItems()
                    ],
                    save_piezo=self.save_piezo.isChecked(),
                    save_command=self.save_command.isChecked(),
                )