# pylint: disable=E0611
from PySide2 import QtGui
from PySide2.QtWidgets import (QDialog, QComboBox, QCheckBox, QPushButton,
QListWidget, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout)


from ascam.constants import TIME_UNIT_FACTORS, CURRENT_UNIT_FACTORS, VOLTAGE_UNIT_FACTORS


# class ExportFADialog(QDialog):
#     def __init__(self):
#         pass


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
        label = QLabel('Time Unit:')
        row_four.addWidget(label)
        self.time_unit_selection = QComboBox()
        self.time_unit_selection.addItems(list(TIME_UNIT_FACTORS.keys()))
        self.time_unit_selection.setCurrentIndex(2)
        self.layout.addLayout(row_four)

        row_five = QHBoxLayout()
        label = QLabel('Current Unit:')
        row_five.addWidget(label)
        self.trace_unit_selection = QComboBox()
        self.trace_unit_selection.addItems(list(CURRENT_UNIT_FACTORS.keys()))
        self.trace_unit_selection.setCurrentIndex(4)
        self.layout.addLayout(row_five)

        row_six = QHBoxLayout()
        label = QLabel('Piezo Unit:')
        row_six.addWidget(label)
        self.piezo_unit_selection = QComboBox()
        self.piezo_unit_selection.addItems(list(VOLTAGE_UNIT_FACTORS.keys()))
        self.piezo_unit_selection.setCurrentIndex(2)
        self.layout.addLayout(row_six)

        row_seven = QHBoxLayout()
        label = QLabel('Command Unit:')
        row_seven.addWidget(label)
        self.command_unit_selection = QComboBox()
        self.command_unit_selection.addItems(list(VOLTAGE_UNIT_FACTORS.keys()))
        self.command_unit_selection.setCurrentIndex(2)
        self.layout.addLayout(row_seven)

        row_eight = QHBoxLayout()
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_click)
        row_eight.addWidget(save_button)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.close)
        row_eight.addWidget(cancel_button)
        self.layout.addLayout(row_eight)

    def save_click(self):
        # if not self.list_selection.selectedItems():
        #     print('empty')
        filename, filetye = QFileDialog.getSaveFileName(
            self, dir=self.main.filename[:-4], filter="Axograph (*.axgd);; Matlab (*.mat)")
        if filename:
            if 'Matlab' in filetye:
                self.main.data.export_matlab(
                    filepath=filename,
                    datakey=self.series_selection.currentText(),
                    lists_to_save=[item.text() for item in self.list_selection.selectedItems()] ,
                    save_piezo=self.save_piezo.isChecked(),
                    save_command=self.save_command.isChecked(),
                    time_unit=self.time_unit.text(),
                    trace_unit=self.trace_unit.text(),
                    piezo_unit=self.piezo_unit.text(),
                    command_unit=self.command_unit.text(),
                    )
            elif 'Axograph' in filetye:
                self.main.data.export_matlab(
                    filepath=filename,
                    datakey=self.series_selection.currentText(),
                    lists_to_save=[item.text() for item in self.list_selection.selectedItems()] ,
                    save_piezo=self.save_piezo.isChecked(),
                    save_command=self.save_command.isChecked(),
                    )

