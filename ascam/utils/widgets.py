from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QHBoxLayout
import pyqtgraph as pg


class TextEdit(QTextEdit):
    def __init__(self, *args, **kwargs):
        QTextEdit.__init__(self, *args, **kwargs)
        self.document().modificationChanged.connect(self.updateMaxHeight)

    def updateMaxHeight(self, *args):
        # the +2 is a bit hacky, but it's there to avoid the appearance of
        # scrollbars when then widget is initialized
        self.setMaximumHeight(self.document().size().height()+2)

    def resizeEvent(self, e):
        QTextEdit.resizeEvent(self, e)
        self.updateMaxHeight()


class CustomViewBox(pg.ViewBox):
    def __init__(self, parent=None):
        # self.setRectMode() # Set mouse mode to rect for convenient zooming
        super().__init__()
        self.exportDialog = None
        self.menu = None # Override pyqtgraph ViewBoxMenu
        self.menu = self.get_menu() # Create the menu

    def raiseContextMenu(self, ev):
        if not self.menuEnabled():
            return
        menu = self.get_menu()
        menu = self.scene().addParentContextMenus(self, menu, ev)
        menu.removeAction(menu.actions()[-2])  # remove the "Plot Options" menu item

        pos  = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))

    def get_menu(self):
        if self.menu is None:
            self.menu = QtGui.QMenu()
            self.viewAll = QtGui.QAction("View All", self.menu)
            self.viewAll.triggered.connect(self.autoRange)
            self.menu.addAction(self.viewAll)

            # self.leftMenu = QtGui.QMenu("Mode clic gauche")
            # group = QtGui.QActionGroup(self)
            # pan = QtGui.QAction(u'Déplacer', self.leftMenu)
            # zoom = QtGui.QAction(u'Zoomer', self.leftMenu)
            # self.leftMenu.addAction(pan)
            # self.leftMenu.addAction(zoom)
            # pan.triggered.connect(self.setPanMode)
            # zoom.triggered.connect(self.setRectMode)
            # pan.setCheckable(True)
            # zoom.setCheckable(True)
            # pan.setActionGroup(group)
            # zoom.setActionGroup(group)
            # self.menu.addMenu(self.leftMenu)
            # self.menu.addSeparator()
        return self.menu

class EventHistConfig(QDialog):
    def __init__(self, parent):
        super.__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def create_widgets(self):
        row = QHBoxLayout()
        label = QLabel("Number of bins:")
        row.addWidget(label)
        self.n_bins = QLineEdit(self.parent)
        row.addWidget(self.n_bins)

        row = QHBoxLayout()
        label = QLabel('Binning Formula')
        row.addWidget(label)
        self.n_bins = QLineEdit(self.parent)
        row.addWidget(self.n_bins)

        row = QHBoxLayout()
        label = QLabel('Time Unit')
        row.addWidget(label)
        self.time_unit = QComboBox()
        self.time_unit.addItems(TIME_UNIT_FACTORS.keys())
        row.addWidget(self.time_unit)

        row = QHBoxLayout()
        label = QLabel('Time Transform')
        row.addWidget(label)
        # self.time_unit = QComboBox()
        # self.time_unit.addItems(TIME_UNIT_FACTORS.keys())
        # row.addWidget(self.time_unit)

        row = QHBoxLayout()
        label = QLabel('Count Transform')
        row.addWidget(label)
        # self.time_unit = QComboBox()
        # self.time_unit.addItems(TIME_UNIT_FACTORS.keys())
        # row.addWidget(self.time_unit)

        row = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.ok_click)
        row.addWidget(ok_button)
        cancel_button = QPushButton("cancel")
        cancel_button.clicked.connect(self.close)
        row.addWidget(cancel_button)

    def ok_click(self):
        # do histogram magic here
        self.close()

