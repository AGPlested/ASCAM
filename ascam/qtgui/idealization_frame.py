import logging

from PySide2.QtWidgets import (QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
        QToolButton, QTabBar, QPushButton, QLabel)


debug_logger = logging.getLogger("ascam.debug")


class IdealizationFrame(QTabWidget):

    def __init__(self):
        super(IdealizationFrame, self).__init__()

        self.tabs = [IdealizationTab(self)]
        self.addTab(self.tabs[0], "1")

        self.insertTab(1, QWidget(), '')
        self.new_button = QToolButton()
        self.new_button.setText('+')
        self.new_button.clicked.connect(self.add_tab)
        self.tabBar().setTabButton(1, QTabBar.RightSide, self.new_button)

        self.setTabsClosable(True)
        self.tabBar().tabCloseRequested.connect(self.removeTab)

    def add_tab(self):
        title = str(self.count())
        debug_logger.debug(f"adding new tab with number {title}")
        tab = IdealizationTab(self)
        self.tabs.append(tab)
        self.insertTab(self.count()-1, tab, title)


class IdealizationTab(QWidget):

    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Idealize me baby"))
        button = QPushButton("bye")
        button.clicked.connect(lambda *args: self.close())
        layout.addWidget(button)
        
