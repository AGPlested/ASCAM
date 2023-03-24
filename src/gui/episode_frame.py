import logging

from PySide2 import QtCore
from PySide2.QtWidgets import (
    QWidget,
    QListWidget,
    QVBoxLayout,
    QSizePolicy,
    QCheckBox,
    QLineEdit,
    QDialog,
    QLabel,
    QPushButton,
    QGridLayout,
    QComboBox,
    QAbstractItemView,
)


debug_logger = logging.getLogger("ascam.debug")
ana_logger = logging.getLogger("ascam.analysis")


class EpisodeFrame(QWidget):
    keyPressed = QtCore.Signal(str)

    def __init__(self, main, *args, **kwargs):
        super(EpisodeFrame, self).__init__(*args, **kwargs)
        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(150)

        self.create_widgets()

        self.keyPressed.connect(self.key_pressed)

    def create_widgets(self):
        self.episode_sets_frame = EpisodeSetsFrame(parent=self, main=self.main)
        self.layout.addWidget(self.episode_sets_frame)

        self.series_selection = QComboBox()
        self.series_selection.setDuplicatesEnabled(False)
        self.series_selection.addItems(list(self.main.data.keys()))
        self.series_selection.currentTextChanged.connect(self.switch_series)
        self.layout.addWidget(self.series_selection)

        self.ep_list = EpisodeList(parent=self, main=self.main)
        self.layout.addWidget(self.ep_list)

    def switch_series(self, index):
        debug_logger.debug(f"switching series to index {index}")
        self.main.data.current_datakey = index
        try:
            self.main.tc_frame.get_params()
            self.main.tc_frame.idealize_episode()
        except AttributeError as e:
            if "'MainWindow' object has no attribute 'tc_frame'" in str(
                e
            ) or "object has no attribute 'get_params'" in str(e):
                pass
            else:
                raise e
        self.main.plot_frame.plot_all()

    def update_combo_box(self):
        self.series_selection.currentTextChanged.disconnect(self.switch_series)
        self.series_selection.clear()
        debug_logger.debug(
            f"updating series selection; new keys are" f"{self.main.data.keys()}"
        )
        self.series_selection.addItems(list(self.main.data.keys()))
        ind = 0
        for k in self.main.data.keys():
            if k == self.main.data.current_datakey:
                break
            ind += 1
        self.series_selection.setCurrentIndex(ind)
        self.series_selection.currentTextChanged.connect(self.switch_series)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPressed.emit(event.text())

    def key_pressed(self, key):
        assigned_keys = [key for (_, key) in self.main.data.episode_sets.values()]
        if key in assigned_keys:
            for ep_set in self.episode_sets_frame.episode_sets:
                if key == ep_set.key:
                    for item in self.ep_list.selectedItems():
                        index = self.ep_list.row(item)
                        self.episode_sets_frame.add_to_set(ep_set.name, index)


class EpisodeSet():
    def __init__(self, main, name: str, key: str | None=None):
        self.main = main
        # self.selected = False
        main.data.add_new_set(name, key)
        self.name = name
        self.key = key
        self.label = f"{name} [{key}]" if key is not None else name
        self.check_box = QCheckBox(self.label)
        self.check_box.setChecked(True)

    def add_episode(self, index):
        self.main.data.add_episodes_to_set(self.name, index)

    def remove_episode(self, index):
        self.main.data.remove_episode_from_set(self.name, index)

    @property
    def episodes(self):
        return self.main.data.episode_sets[self.name][0]


class EpisodeSetsFrame(QWidget):
    keyPressed = QtCore.Signal(str)

    def __init__(self, parent, main, *args, **kwargs):
        super(EpisodeSetsFrame, self).__init__(*args, **kwargs)
        self.parent = parent
        self.main = main
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.episode_sets = []
        self.new_set("All")

        self.new_button = QPushButton("New List")
        # self.new_button.clicked.connect(self.create_dialog)
        self.new_button.clicked.connect(self.new_set_button)
        self.layout.addWidget(self.new_button)

    def new_set_button(self):
        name, key = NewSetDialog.get_new_set(self)
        self.new_set(name, key)

    def new_set(self, name: str, key=None):
        new_set = EpisodeSet(self.main, name, key)
        self.episode_sets.append(new_set)
        self.layout.insertWidget(0, new_set.check_box)
        self.main.data.add_new_set(name, key)

    def get_set(self, name: str) -> EpisodeSet:
        return [x for x in self.episode_sets if x.name == name][0]

    def add_to_set(self, name: str, index: int):
        if not self.main.data.index_is_in_set(index=index, name=name):
            self.get_set(name).add_episode(index)
        else:
            self.get_set(name).remove_episode(index)
        self.updatet_episode_name(index)

    def updatet_episode_name(self, index: int):
        """Updates the name of the episode at position `index` to include the
        correct keys."""
        assigned_keys = self.main.data.get_episode_keys(index)
        ep_display_name = f"Episode {self.main.data.series[index].n_episode} "
        s = "".join([f"[{k}]" for k in assigned_keys])
        ep_display_name += s.rjust(20 - len(ep_display_name), " ")
        self.parent.ep_list.item(index).setText(ep_display_name)

    def create_dialog(self):
        self.dialog = QDialog()
        self.dialog.setWindowTitle("Add List")
        layout = QGridLayout()
        self.dialog.setLayout(layout)

        layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_entry = QLineEdit()
        layout.addWidget(self.name_entry, 0, 1)
        layout.addWidget(QLabel("Key:"), 1, 0)
        self.key_entry = QLineEdit()
        self.key_entry.setMaxLength(1)
        layout.addWidget(self.key_entry, 1, 1)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_clicked)
        layout.addWidget(ok_button, 2, 0)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.dialog.close)
        layout.addWidget(cancel_button, 2, 1)
        self.dialog.exec_()

    def keyPressEvent(self, event):
        if event.text().isalpha():
            event.ignore()
        else:
            super().keyPressEvent(event)


class NewSetDialog(QDialog):
   def __init__(self, parent):
       self.parent = parent
       self.setWindowTitle("Add List")
       layout = QGridLayout()
       self.setLayout(layout)

       layout.addWidget(QLabel("Name:"), 0, 0)
       name_entry = QLineEdit()
       layout.addWidget(name_entry, 0, 1)
       layout.addWidget(QLabel("Key:"), 1, 0)
       key_entry = QLineEdit()
       key_entry.setMaxLength(1)
       layout.addWidget(key_entry, 1, 1)

       ok_button = QPushButton("OK")
       ok_button.clicked.connect(self.ok_clicked)
       layout.addWidget(ok_button, 2, 0)

       cancel_button = QPushButton("Cancel")
       cancel_button.clicked.connect(self.close)
       layout.addWidget(cancel_button, 2, 1)
       self.exec_()

   def ok_clicked(self):
       self.parent.new_set(self.name_entry.text(), self.key_entry.text())
       self.close()

   @classmethod
   def get_new_set(cls, parent):
       dialog = cls(parent)
       dialog.exec_()
       return dialog.name, dialog.key


class EpisodeList(QListWidget):
    """Widget holding the scrollable list of episodes and the episode list
    selection"""

    keyPressed = QtCore.Signal(str)

    def __init__(self, parent, main, *args, **kwargs):
        super(EpisodeList, self).__init__(*args, **kwargs)
        self.parent = parent
        self.main = main
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.currentItemChanged.connect(
            self.on_item_click, type=QtCore.Qt.DirectConnection
        )
        self.populate()

    def on_item_click(self, item, _):
        debug_logger.debug(f"clicked new episode")
        ep_number = int(item.text().split()[1])
        self.main.data.current_ep_ind = ep_number

    def populate(self):
        self.currentItemChanged.disconnect(self.on_item_click)
        self.clear()
        if self.main.data is not None:
            debug_logger.debug("inserting data")
            self.addItems(
                [f"Episode {e.n_episode}" for e in self.main.data.series]
            )
        self.setCurrentRow(0)
        self.currentItemChanged.connect(
            self.on_item_click, type=QtCore.Qt.DirectConnection
        )

    def keyPressEvent(self, event):
        if event.text().isalpha():
            event.ignore()
        else:
            super().keyPressEvent(event)
