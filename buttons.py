from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QCursor, QFont


class DraggableButton(QPushButton):
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setFixedSize(60, 60)
        font = QFont("Arial", 32)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2c;
                padding: 0px;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 10px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """)
        self.dragging = False
        self.offset = QPoint()
        self.was_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.was_dragging = False
            self.offset = event.globalPos() - self.window().pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.window().move(QCursor.pos() - self.offset)
            self.was_dragging = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        super().mouseReleaseEvent(event)
