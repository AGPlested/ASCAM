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
<<<<<<< HEAD
=======
    QHBoxLayout,
>>>>>>> subsets
)


from ..core import Recording
<<<<<<< HEAD
=======
from ..constants import TIME_UNIT_FACTORS, CURRENT_UNIT_FACTORS, VOLTAGE_UNIT_FACTORS
>>>>>>> subsets
from ..utils.widgets import EntryWidget


class BaseExportWidget(EntryWidget):
    def __init__(
        self,
        main,
        dialog=None,
        default_time_unit="s",
        default_trace_unit="A",
        default_piezo_unit="V",
        default_command_unit="V",
    ):
        self.main = main
        self.dialog = dialog
        self.create_selection_widgets()
        super().__init__(
            main,
            default_time_unit=default_time_unit,
            default_trace_unit=default_trace_unit,
            default_piezo_unit=default_piezo_unit,
            default_command_unit=default_command_unit,
        )

    def create_selection_widgets(self):
        self.series_selection = QComboBox()
        self.series_selection.addItems(list(self.main.data.keys()))
        self.series_selection.setCurrentText(self.main.data.current_datakey)

        self.list_selection = QListWidget()
        self.list_selection.addItems(list(self.main.data.lists.keys()))
        self.list_selection.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.list_selection.setCurrentRow(0)
        self.list_selection.setFixedHeight(18 * len(list(self.main.data.lists.keys())))


class ExportFADialog(QDialog):
    def __init__(self, main):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(ExportFAWidget(main, self))

        self.exec_()


class ExportFAWidget(BaseExportWidget):
    def __init__(self, main, dialog):
        self.main = main
        super().__init__(main, dialog)

    def create_widgets(self):
        self.add_row(self.series_selection)

        self.add_row(QLabel("Lists to export:"))
        self.add_row(self.list_selection)

        self.add_row(QLabel("Time Unit:"), self.time_unit_entry)

        self.add_row(QLabel("Current Unit:"), self.trace_unit_entry)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_click)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.dialog.close)
        self.add_row(save_button, cancel_button)

    def save_click(self):
        filename, filetye = QFileDialog.getSaveFileName(
            self,
            dir=self.main.filename[:-4] + "_first_activation",
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
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(OpenFileEntryWidget(main, filename, self))
        self.setFixedWidth(300)

        self.exec_()


class OpenFileEntryWidget(EntryWidget):
    def __init__(self, main, filename, dialog):
        self.main = main
        self.filename = filename
        self.dialog = dialog
        super().__init__(
            main,
            default_time_unit="s",
            default_trace_unit="A",
            default_piezo_unit="V",
            default_command_unit="V",
        )

    def create_widgets(self):
        file_button = QLabel("File:")
        self.file_name_label = QLabel(self.filename)
        self.add_row(file_button, self.file_name_label)

        sampling_label = QLabel("Sampling rate [Hz]")
        self.sampling_entry = QLineEdit("40000")
        self.add_row(sampling_label, self.sampling_entry)

        t_unit_label = QLabel("Time unit")
        self.add_row(t_unit_label, self.time_unit_entry)
        self.time_unit_entry.setToolTip("Select the units that are used in the file.")
        t_unit_label.setToolTip("Select the units that are used in the file.")

        t_unit_label = QLabel("Current unit")
        self.add_row(t_unit_label, self.trace_unit_entry)
        self.trace_unit_entry.setToolTip("Select the units that are used in the file.")
        t_unit_label.setToolTip("Select the units that are used in the file.")

        t_unit_label = QLabel("Piezo unit")
        self.add_row(t_unit_label, self.piezo_unit_entry)
        self.piezo_unit_entry.setToolTip("Select the units that are used in the file.")
        t_unit_label.setToolTip("Select the units that are used in the file.")

        t_unit_label = QLabel("Command unit")
        self.add_row(t_unit_label, self.command_unit_entry)
        self.command_unit_entry.setToolTip(
            "Select the units that are used in the file."
        )
        t_unit_label.setToolTip("Select the units that are used in the file.")

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_clicked)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.dialog.close)
        self.add_row(ok_button, cancel_button)

    def ok_clicked(self):
        self.main.data = Recording.from_file(
            filename=self.main.filename,
            sampling_rate=self.sampling_entry.text(),
            time_input_unit=self.time_unit,
            trace_input_unit=self.trace_unit,
            piezo_input_unit=self.piezo_unit,
            command_input_unit=self.command_unit,
        )
        self.main.ep_frame.ep_list.populate()
        self.main.ep_frame.update_combo_box()
        self.main.ep_frame.setFocus()
        self.main.plot_frame.plot_all()
        self.main.setWindowTitle(f"cuteSCAM {self.main.filename}")
        self.dialog.close()
        self.close()


class ExportDialog(QDialog):
    def __init__(self, main):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(ExportWidget(main, self))
        self.setFixedWidth(300)

        self.exec_()


class ExportWidget(BaseExportWidget):
    def __init__(self, main, dialog):
        self.main = main
        super().__init__(main, dialog)

    def create_widgets(self):
        self.add_row(self.series_selection)

        self.save_piezo = QCheckBox("Export Piezo Data")
        self.save_command = QCheckBox("Export Command Voltage")
        self.add_row(self.save_piezo, self.save_command)

        self.add_row(QLabel("Lists to export:"))
        self.add_row(self.list_selection)

        self.add_row(QLabel("Time Unit:"), self.time_unit_entry)

        self.add_row(QLabel("Current Unit:"), self.trace_unit_entry)

        self.add_row(QLabel("Piezo Unit:"), self.piezo_unit_entry)

        self.add_row(QLabel("Command Unit:"), self.command_unit_entry)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_click)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.dialog.close)
        self.add_row(save_button, cancel_button)

    def save_click(self):
        filename, filetype = QFileDialog.getSaveFileName(
            self,
            dir=self.main.filename[:-4],
            filter="Axograph (*.axgd);; Matlab (*.mat)",
        )
        if filename:
            if "Matlab" in filetype:
                self.main.data.export_matlab(
                    filepath=filename,
                    datakey=self.series_selection.currentText(),
                    lists_to_save=[
                        item.text() for item in self.list_selection.selectedItems()
                    ],
                    save_piezo=self.save_piezo.isChecked(),
                    save_command=self.save_command.isChecked(),
                    time_unit=self.time_unit,
                    trace_unit=self.trace_unit,
                    piezo_unit=self.piezo_unit,
                    command_unit=self.command_unit,
                )
            elif "Axograph" in filetype:
                self.main.data.export_axo(
                    filepath=filename,
                    datakey=self.series_selection.currentText(),
                    lists_to_save=[
                        item.text() for item in self.list_selection.selectedItems()
                    ],
                    save_piezo=self.save_piezo.isChecked(),
                    save_command=self.save_command.isChecked(),
                )
        self.dialog.close()


class ExportIdealizationDialog(QDialog):
    def __init__(self, main, id_cache):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(ExportIdealizationWidget(main, self, id_cache))
        self.setFixedWidth(300)

        self.exec_()


class ExportIdealizationWidget(BaseExportWidget):
    def __init__(self, main, dialog, id_cache):
        self.main = main
        self.id_cache = id_cache
        super().__init__(main, dialog)

    def create_widgets(self):
        self.add_row(QLabel("Lists to export:"))
        self.add_row(self.list_selection)

        self.add_row(QLabel("Time Unit:"), self.time_unit_entry)

        self.add_row(QLabel("Current Unit:"), self.trace_unit_entry)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_click)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.dialog.close)
        self.add_row(save_button, cancel_button)

    def save_click(self):
        filename, filetye = QFileDialog.getSaveFileName(
            self, dir=self.main.filename[:-4], filter="CSV (*.csv)"
        )
        self.main.data.export_idealization(
            filename,
            time_unit=self.time_unit,
            trace_unit=self.trace_unit,
            lists_to_save=[item.text() for item in self.list_selection.selectedItems()],
            amplitudes=self.id_cache.amplitudes,
            thresholds=self.id_cache.thresholds,
            resolution=self.id_cache.resolution,
            interpolation_factor=self.id_cache.interpolation_factor,
        )

        self.dialog.close()
