from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import QTextEdit
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
        self.menu = self.getMenu() # Create the menu

    def raiseContextMenu(self, ev):
        if not self.menuEnabled():
            return
        menu = self.getMenu()
        menu = self.scene().addParentContextMenus(self, menu, ev)
        menu.removeAction(menu.actions()[-2])  # remove the "Plot Options" menu item

        pos  = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))

    def getMenu(self):
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

