import logging

from PySide2.QtWidgets import (QWidget, QListWidget, QVBoxLayout, QSizePolicy, 
 QCheckBox,QLineEdit,                 QDialog,QLabel,         QPushButton,    QGridLayout, QComboBox)


debug_logger = logging.getLogger("ascam.debug")


class EpisodeFrame(QWidget):
    def __init__(self, main, *args, **kwargs):
        super(EpisodeFrame, self).__init__(*args, **kwargs)
        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_widgets()
        
    def create_widgets(self):
        self.list_frame = ListFrame(self)
        self.layout.addWidget(self.list_frame)

        self.series_selection = QComboBox()
        self.series_selection.setDuplicatesEnabled(False)
        self.series_selection.addItems(self.main.data.keys())
        self.series_selection.currentTextChanged.connect(self.switch_series)
        self.layout.addWidget(self.series_selection)

        self.ep_list = EpisodeList(self)
        self.layout.addWidget(self.ep_list)

    def switch_series(self, index):
        debug_logger.debug(f"switching series to index {index}")
        self.main.data.current_datakey = index
        self.main.plot_frame.plot_all()

    def update_combo_box(self):
        self.series_selection.currentTextChanged.disconnect(self.switch_series)
        self.series_selection.clear()
        debug_logger.debug(f"updating series selection; new keys are"
                           f"{self.main.data.keys()}")
        self.series_selection.addItems(self.main.data.keys())
        ind = 0
        for k in self.main.data.keys():
            if k == self.main.data.current_datakey:
                break
            ind += 1
        self.series_selection.setCurrentIndex(ind)
        self.series_selection.currentTextChanged.connect(self.switch_series)


class ListFrame(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(ListFrame, self).__init__(*args, **kwargs)
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.lists = []
        self.new_list('All')

        self.new_button = QPushButton("New List")
        self.new_button.clicked.connect(self.create_widgets)
        self.layout.addWidget(self.new_button)

    def new_list(self, name, key=None):
        label = f'{name} [{key}]' if key is not None else name
        check_box = QCheckBox(label)
        self.lists.append(check_box)
        self.layout.insertWidget(0, check_box)

    def create_widgets(self):
        self.dialog = QDialog()
        self.dialog.setWindowTitle("Add List")
        layout = QGridLayout()
        self.dialog.setLayout(layout)

        layout.addWidget(QLabel('Name:'), 0, 0)
        self.name_entry = QLineEdit()
        layout.addWidget(self.name_entry, 0, 1)
        layout.addWidget(QLabel('Key:'), 1, 0)
        self.key_entry = QLineEdit()
        self.key_entry.setMaxLength(1)
        layout.addWidget(self.key_entry, 1, 1)

        ok_button = QPushButton('Ok')
        ok_button.clicked.connect(self.ok_clicked)
        layout.addWidget(ok_button, 2, 0)

        cancel_button = QPushButton('cancel')
        cancel_button.clicked.connect(self.close)
        layout.addWidget(cancel_button, 2, 1)
        self.dialog.exec_()

    def ok_clicked(self):
        self.new_list(self.name_entry.text(), self.key_entry.text())
        self.dialog.close()


class EpisodeList(QListWidget):
    """Widget holding the scrollable list of episodes and the episode list
    selection"""

    def __init__(self, parent, *args, **kwargs):
        super(EpisodeList, self).__init__(*args, **kwargs)
        self.parent = parent
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.currentItemChanged.connect(self.on_item_click)
        self.populate()

    def on_item_click(self, item, previous):
        self.parent.main.data.current_ep_ind = self.row(item)
        try:
            self.parent.main.tc_frame.idealize_episode()
        except AttributeError:
            pass
        self.parent.main.plot_frame.update_plots()

    def populate(self):
        self.currentItemChanged.disconnect(self.on_item_click)
        self.clear()
        if self.parent.main.data is not None:
            n_eps = len(self.parent.main.data.series)
            debug_logger.debug("inserting data")
            self.addItems([f"Episode {i+1}" for i in range(n_eps)])
        self.setCurrentRow(0)
        self.currentItemChanged.connect(self.on_item_click)
