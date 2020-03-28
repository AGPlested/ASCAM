from PySide2.QtWidgets import QTextEdit


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

