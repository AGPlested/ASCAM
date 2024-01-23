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
<<<<<<< HEAD
        self.list_frame = ListFrame(self)
        self.layout.addWidget(self.list_frame)

=======
        self.subset_frame = SubsetFrame(self)
        self.layout.addWidget(self.subset_frame)

            
        ### this box selects which series (according to processing)
>>>>>>> subsets
        self.series_selection = QComboBox()
        self.series_selection.setDuplicatesEnabled(False)
        self.series_selection.addItems(list(self.main.data.keys()))
        self.series_selection.currentTextChanged.connect(self.switch_series)
        self.layout.addWidget(self.series_selection)

        self.ep_list = EpisodeList(self)
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
<<<<<<< HEAD
        assigned_keys = [x[1] for x in self.main.data.lists.values()]
        if key in assigned_keys:
            for l in self.list_frame.lists:
=======
        assigned_keys = [x[1] for x in self.main.data.subsets.values()]
        if key in assigned_keys:
            for l in self.subset_frame.subsets:
>>>>>>> subsets
                if f"[{key}]" in l.text():
                    name = l.text().split()[0]
                    for item in self.ep_list.selectedItems():
                        index = self.ep_list.row(item)
<<<<<<< HEAD
                        self.list_frame.add_to_list(name, key, index)


class ListFrame(QWidget):
    keyPressed = QtCore.Signal(str)

    def __init__(self, parent, *args, **kwargs):
        super(ListFrame, self).__init__(*args, **kwargs)
=======
                        self.subset_frame.add_to_subset(name, key, index)


class SubsetFrame(QWidget):
    keyPressed = QtCore.Signal(str)

    def __init__(self, parent, *args, **kwargs):
        super(SubsetFrame, self).__init__(*args, **kwargs)
>>>>>>> subsets
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

<<<<<<< HEAD
        self.lists = []
        self.new_list("All")

        self.new_button = QPushButton("New List")
        self.new_button.clicked.connect(self.create_dialog)
        self.layout.addWidget(self.new_button)

    def new_list(self, name, key=None):
        label = f"{name} [{key}]" if key is not None else name
        check_box = QCheckBox(label)
        check_box.setChecked(True)
        self.lists.append(check_box)
        self.layout.insertWidget(0, check_box)
        self.parent.main.data.lists[name] = ([], key)
        debug_logger.debug(
            f"added list '{name}' with key '{key}'\n"
            "lists are now:\n"
            f"{self.parent.main.data.lists}"
        )

    def add_to_list(self, name, key, index):
        if index not in self.parent.main.data.lists[name][0]:
            self.parent.main.data.lists[name][0].append(index)
            assigned_keys = [
                x[1]
                for x in self.parent.main.data.lists.values()
=======
        self.subsets = []
        self.new_subset("All", checked_state=True)

        self.new_button = QPushButton("New Subset")
        self.new_button.clicked.connect(self.create_dialog)
        self.layout.addWidget(self.new_button)

    def new_subset(self, name, key=None, checked_state=False):
        label = f"{name} [{key}]" if key is not None else name
        sub_check_box = QCheckBox(label)
        sub_check_box.setChecked(checked_state)
        sub_check_box.stateChanged.connect(self.subset_click)
        self.subsets.append(sub_check_box)
        self.layout.insertWidget(0, sub_check_box)
        # create an empty subset
        self.parent.main.data.subsets[name] = ([], key)
        debug_logger.debug(
            f"added subset '{name}' with keypress '{key}'\n"
            "subsets are now:\n"
            f"{self.parent.main.data.subsets}"
        )

    def subsets_check(self):
        
        checked_list =[]
        unchecked_list =[]
        
        for b in self.subsets:
            if b.isChecked():
                checked_list.append(b.text().split(" ")[0])
            else :
                unchecked_list.append(b.text().split(" ")[0])
            
        return checked_list, unchecked_list

    def subset_click(self, state):
        print("clicked state", state, self.sender().text())
        checked_list,unchecked_list = self.subsets_check()
        
        print("Checked subset boxes:", checked_list)
        print("Unchecked subset boxes:", unchecked_list)
        self.parent.ep_list.populate()

    def add_to_subset(self, name, key, index):
        # unfortunately this adds on list index not on actually clicked episode
        # also tags letters do not refresh with episode list
        if index not in self.parent.main.data.subsets[name][0]:
            self.parent.main.data.subsets[name][0].append(index)
            assigned_keys = [
                x[1]
                for x in self.parent.main.data.subsets.values()
>>>>>>> subsets
                if index in x[0] and x[1] is not None
            ]
            n = f"Episode {self.parent.main.data.series[index].n_episode} "
            assigned_keys.sort()
            s = ""
            for k in assigned_keys:
                if k is not None:
                    s += f"[{k}]"
            n += s.rjust(20 - len(n), " ")
            self.parent.ep_list.item(index).setText(n)
            ana_logger.debug(
<<<<<<< HEAD
                f"added episode {self.parent.main.data.series[index].n_episode} to list {name}"
            )
        else:
            self.parent.main.data.lists[name][0].remove(index)
            n = self.parent.ep_list.item(index).text()
            assigned_keys = [
                x[1]
                for x in self.parent.main.data.lists.values()
=======
                f"added episode {self.parent.main.data.series[index].n_episode} to subset {name}"
            )
        else:
            self.parent.main.data.subsets[name][0].remove(index)
            n = self.parent.ep_list.item(index).text()
            assigned_keys = [
                x[1]
                for x in self.parent.main.data.subsets.values()
>>>>>>> subsets
                if index in x[0] and x[1] is not None
            ]
            assigned_keys.sort()
            n = f"Episode {self.parent.main.data.series[index].n_episode} "
            s = ""
            for k in assigned_keys:
                if k is not None:
                    s += f"[{k}]"
            n += s.rjust(20 - len(n), " ")
            self.parent.ep_list.item(index).setText(n)
            ana_logger.debug(
<<<<<<< HEAD
                f"removed episode {self.parent.main.data.series[index].n_episode} from list {name}"
=======
                f"removed episode {self.parent.main.data.series[index].n_episode} from subset {name}"
>>>>>>> subsets
            )

    def create_dialog(self):
        self.dialog = QDialog()
<<<<<<< HEAD
        self.dialog.setWindowTitle("Add List")
=======
        self.dialog.setWindowTitle("Add subset")
>>>>>>> subsets
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

    def ok_clicked(self):
<<<<<<< HEAD
        self.new_list(self.name_entry.text(), self.key_entry.text())
=======
        self.new_subset(self.name_entry.text(), self.key_entry.text())
>>>>>>> subsets
        self.dialog.close()

    def keyPressEvent(self, event):
        if event.text().isalpha():
            event.ignore()
        else:
            super().keyPressEvent(event)


class EpisodeList(QListWidget):
    """Widget holding the scrollable list of episodes and the episode list
    selection"""

    keyPressed = QtCore.Signal(str)

    def __init__(self, parent, *args, **kwargs):
        super(EpisodeList, self).__init__(*args, **kwargs)
        self.parent = parent
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.currentItemChanged.connect(
            self.on_item_click, type=QtCore.Qt.DirectConnection
        )
        self.populate()

    def on_item_click(self, item, _):
        debug_logger.debug(f"clicked new episode")
        ep_number = int(item.text().split()[1])
        self.parent.main.data.current_ep_ind = ep_number

    def populate(self):
        self.currentItemChanged.disconnect(self.on_item_click)
        self.clear()
        if self.parent.main.data is not None:
<<<<<<< HEAD
            debug_logger.debug("inserting data")
            self.addItems(
                [f"Episode {e.n_episode}" for e in self.parent.main.data.series]
            )
=======
            selected_subsets,_ = self.parent.subset_frame.subsets_check()
            episodes = self.parent.main.data.episodes_in_subsets(selected_subsets)
            if episodes is not None:
                debug_logger.debug("inserting data")
                self.addItems(
                    [f"Episode {e.n_episode}" for e in episodes]
                )
>>>>>>> subsets
        self.setCurrentRow(0)
        self.currentItemChanged.connect(
            self.on_item_click, type=QtCore.Qt.DirectConnection
        )

    def keyPressEvent(self, event):
        if event.text().isalpha():
            event.ignore()
        else:
            super().keyPressEvent(event)
