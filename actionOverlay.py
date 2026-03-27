import sys
import os
import pyautogui
import win32gui
import win32con
from PyQt5.QtCore import Qt, QPoint, QRect, QObject
from PyQt5.QtWidgets import QSlider
import datetime
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QTimer
from notifypy import Notify
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSizePolicy, QSizeGrip)
from PyQt5.QtGui import (QCursor, QFont, QPainter, QPen, QColor, QPixmap, 
                         QMouseEvent, QPaintEvent, QIcon)

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

class DrawingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("actionOverlay - Drawing Window")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(32)
        self.title_bar.setStyleSheet("background-color: #333;")

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)

        title_layout.addStretch()

        self.bucket_button = QPushButton("🪣")
        self.bucket_button.setFixedSize(32, 32)
        self.bucket_button.setCheckable(True)
        self.bucket_button.setToolTip("Fill Bucket")
        self.bucket_button.setStyleSheet("""
            QPushButton {
                background-color: #eee;
                color: #222;
                border: 2px solid #222;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:checked {
                background-color: #fff;
                border: 2px solid #FFD600;
                color: #FFD600;
            }
        """)
        self.bucket_button.clicked.connect(self.set_bucket_mode)
        title_layout.addWidget(self.bucket_button)

        self.color_picker_button = QPushButton("🎨")
        self.color_picker_button.setFixedSize(32, 32)
        self.color_picker_button.setToolTip("Pick color from anywhere")
        self.color_picker_button.setStyleSheet("""
            QPushButton {
                background-color: #eee;
                color: #222;
                border: 2px solid #222;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:pressed {
                background-color: #fff;
                border: 2px solid #2196F3;
                color: #2196F3;
            }
        """)
        self.color_picker_button.clicked.connect(self.pick_color_from_screen)
        title_layout.addWidget(self.color_picker_button)

        self.undo_button = QPushButton("↶")
        self.undo_button.setFixedSize(32, 32)
        self.undo_button.setToolTip("Undo (Ctrl+Z)")
        self.undo_button.setEnabled(False)
        self.undo_button.setStyleSheet("""
            QPushButton { background-color: #eee; color: #222; border: 2px solid #222; border-radius: 4px; font-size: 18px; }
            QPushButton:disabled { background-color: #555; color: #999; border-color: #444; }
        """)
        self.undo_button.clicked.connect(self.undo)
        title_layout.addWidget(self.undo_button)

        self.redo_button = QPushButton("↷")
        self.redo_button.setFixedSize(32, 32)
        self.redo_button.setToolTip("Redo (Ctrl+Y)")
        self.redo_button.setEnabled(False)
        self.redo_button.setStyleSheet("""
            QPushButton { background-color: #eee; color: #222; border: 2px solid #222; border-radius: 4px; font-size: 18px; }
            QPushButton:disabled { background-color: #555; color: #999; border-color: #444; }
        """)
        self.redo_button.clicked.connect(self.redo)
        title_layout.addWidget(self.redo_button)

        # sepparator
        sep = QWidget()
        sep.setFixedWidth(2)
        sep.setFixedHeight(24)
        sep.setStyleSheet("background-color: #fff; margin-left: 6px; margin-right: 6px; border-radius: 1px;")
        title_layout.addWidget(sep)

        self.eraser_button = QPushButton("⎚")
        self.eraser_button.setFixedSize(32, 32)
        self.eraser_button.setCheckable(True)
        self.eraser_button.setToolTip("Eraser")
        self.eraser_button.setStyleSheet("""
            QPushButton {
                background-color: #eee;
                color: #222;
                border: 2px solid #222;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:checked {
                background-color: #fff;
                border: 2px solid #2196F3;
                color: #2196F3;
            }
        """)
        self.eraser_button.clicked.connect(self.set_eraser_mode)
        title_layout.addWidget(self.eraser_button)

        self.color_buttons = []
        color_defs = [
            ("#FFD600", "yellow"),
            ("#FF9800", "orange"),
            ("#F44336", "red"),
            ("#B71C1C", "dark red"),
            ("#E91E63", "pink"),
            ("#880E4F", "dark pink"),
            ("#9C27B0", "purple"),
            ("#4A148C", "dark purple"),
            ("#0D47A1", "dark blue"),
            ("#00BCD4", "cyan"),
            ("#006064", "dark cyan"),
            ("#4CAF50", "green"),
            ("#1B5E20", "dark green"),
            ("#8D5524", "brown"),
            ("#212121", "dark gray"),
            ("#FFFFFF", "white"),
            ("#000000", "black"),
        ]
        self.pen = QPen(QColor(255, 255, 255), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        def make_color_btn(color, tooltip):
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid #222;
                    border-radius: 4px;
                }}
                QPushButton:checked {{
                    border: 2px solid #fff;
                }}
            """)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, c=color: self.set_pen_color(c))
            return btn

        self.color_btn_group = []
        for color, name in color_defs:
            btn = make_color_btn(color, name)
            self.color_buttons.append(btn)
            title_layout.addWidget(btn)
            self.color_btn_group.append(btn)
        self.color_btn_group[2].setChecked(True)

        # sepparator
        sep = QWidget()
        sep.setFixedWidth(2)
        sep.setFixedHeight(24)
        sep.setStyleSheet("background-color: #fff; margin-left: 6px; margin-right: 6px; border-radius: 1px;")
        title_layout.addWidget(sep)

        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setMinimum(1)
        self.thickness_slider.setMaximum(100)
        self.thickness_slider.setValue(3)
        self.thickness_slider.setFixedWidth(100)
        self.thickness_slider.setToolTip("Pen thickness")
        self.thickness_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 22px;
                background: transparent;
                margin: 0px;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #2196F3;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #222;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #fff;
                border: 2px solid #2196F3;
                width: 22px;
                margin: -7px 0;
                border-radius: 4px;
            }
        """)
        self.thickness_slider.valueChanged.connect(self.set_pen_thickness)
        title_layout.addWidget(self.thickness_slider)

        title_layout.addStretch()

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                color: white;
                border: 1px solid #000;
                background-color: #ff0000;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.close_button.clicked.connect(self.close)

        self.clear_button = QPushButton("CLR")
        self.clear_button.setFixedSize(40, 30)
        self.clear_button.setStyleSheet("""
            QPushButton {
                color: white;
                border: 1px solid #000;
                background-color: #f47c36;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.clear_button.setToolTip("Clear the drawing")
        self.clear_button.clicked.connect(self.clear_drawing)

        self.print_screen_button = QPushButton("⌜⌟", self)
        self.print_screen_button.setFixedSize(30, 30)
        self.print_screen_button.setStyleSheet("""
            QPushButton {
                color: white;
                border: 1px solid #000;
                background-color: #2196F3;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.print_screen_button.setToolTip("Print Screen")
        self.print_screen_button.clicked.connect(self.take_screenshot)

        self.download_button = QPushButton("↓", self)
        self.download_button.setFixedSize(30, 30)
        self.download_button.setStyleSheet("""
            QPushButton {
                color: white;
                border: 1px solid #000;
                background-color: #4CAF50;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.download_button.setToolTip("Download the drawing as PNG")
        self.download_button.clicked.connect(self.save_as_png)

        title_layout.addWidget(self.print_screen_button)
        title_layout.addWidget(self.download_button)
        title_layout.addWidget(self.clear_button)
        title_layout.addWidget(self.close_button)
        layout.addWidget(self.title_bar)

        self.drawing_label = QLabel(self)
        self.drawing_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.drawing_label.setStyleSheet("background-color: rgba(30, 30, 30, 20);")
        layout.addWidget(self.drawing_label)

        self.pixmap = QPixmap(1, 1)
        self.pixmap.fill(Qt.transparent)
        self.last_point = None

        self.history = []
        self.future = []

        self.dragging = False
        self.offset = QPoint()

        self.setFocusPolicy(Qt.StrongFocus)

        self.drawing_label.showEvent = self.update_drawing_surface

        self.showEvent = self.set_available_geometry_on_show

        self.eraser_mode = False
        self.bucket_mode = False
        self._color_picker_active = False

    def pick_color_from_screen(self):
        # If bucket mode is active, deactivate it
        if self.bucket_button.isChecked():
            self.bucket_button.setChecked(False)
            self.set_bucket_mode()
        if self._color_picker_active:
            return
        QApplication.processEvents()
        self._color_picker_active = True

        self.color_picker_button.setStyleSheet("""
            QPushButton {
                background-color: #eee;
                color: #222;
                border: 2px solid #FFA500;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:pressed {
                background-color: #fff;
                border: 2px solid #2196F3;
                color: #2196F3;
            }
        """)

        def on_click(event):
            if self._color_picker_active and event.button() == Qt.LeftButton:
                pos = QCursor.pos()
                color = self.get_pixel_color(pos)
                if color:
                    self.set_pen_color(color.name())
                    for btn in self.color_btn_group:
                        btn.setChecked(False)
                    self.eraser_button.setChecked(False)
                    self.color_picker_button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {color.name()};
                            color: #222;
                            border: 2px solid #222;
                            border-radius: 4px;
                            font-size: 16px;
                        }}
                        QPushButton:pressed {{
                            background-color: #fff;
                            border: 2px solid #2196F3;
                            color: #2196F3;
                        }}
                    """)
                self._color_picker_active = False
                QApplication.instance().removeEventFilter(self._mouse_event_filter)
                self.activateWindow()
            return False

        class MouseEventFilter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QMouseEvent.MouseButtonPress:
                    return on_click(event)
                return False

        self._mouse_event_filter = MouseEventFilter()
        QApplication.instance().installEventFilter(self._mouse_event_filter)

    def get_pixel_color(self, pos):
        screen = QApplication.screenAt(pos)
        if not screen:
            screen = QApplication.primaryScreen()
        if not screen:
            return None
        pixmap = screen.grabWindow(0, pos.x(), pos.y(), 1, 1)
        if pixmap.isNull():
            return None
        image = pixmap.toImage()
        if image.isNull():
            return None
        color = QColor(image.pixel(0, 0))
        return color

    def save_as_png(self):
        if self.pixmap.isNull():
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Drawing as PNG", "drawing.png", "PNG Files (*.png)")
        if file_path:
            from PyQt5.QtGui import QImage
            image = self.pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
            image.save(file_path, "PNG")

    def take_screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')

    def set_eraser_mode(self):
        if self.eraser_button.isChecked():
            self.eraser_mode = True
            for btn in self.color_btn_group:
                btn.setChecked(False)
            self.pen.setColor(Qt.transparent)
            self.pen.setWidth(self.thickness_slider.value())
        else:
            self.eraser_mode = False
            checked = [btn for btn in self.color_btn_group if btn.isChecked()]
            if checked:
                idx = self.color_btn_group.index(checked[0])
                color = self.color_buttons[idx].palette().button().color()
                self.pen.setColor(color)
            else:
                self.pen.setColor(QColor("#FFFFFF"))
            self.pen.setWidth(self.thickness_slider.value())

    def set_bucket_mode(self):
        if self.bucket_button.isChecked():
            # If color picker is active, deactivate it
            if self._color_picker_active:
                self._color_picker_active = False
                self.color_picker_button.setStyleSheet("""
                    QPushButton {
                        background-color: #eee;
                        color: #222;
                        border: 2px solid #222;
                        border-radius: 4px;
                        font-size: 16px;
                    }
                    QPushButton:pressed {
                        background-color: #fff;
                        border: 2px solid #2196F3;
                        color: #2196F3;
                    }
                """)
                try:
                    QApplication.instance().removeEventFilter(self._mouse_event_filter)
                except Exception:
                    pass
            self.bucket_mode = True
        else:
            self.bucket_mode = False

    def set_pen_color(self, color):
        self.eraser_button.setChecked(False)
        self.eraser_mode = False
        for btn in self.color_btn_group:
            btn.setChecked(False)
        sender = self.sender()
        if sender:
            sender.setChecked(True)
        self.pen.setColor(QColor(color))
        self.pen.setWidth(self.thickness_slider.value())

    def set_pen_thickness(self, value):
        self.pen.setWidth(value)

    def set_available_geometry_on_show(self, event):
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen:
            geometry = screen.availableGeometry()
            self.setGeometry(geometry)
        event.accept()

    def set_fullscreen_on_show(self, event):
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen:
            geometry = screen.geometry()
            self.setGeometry(geometry)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.title_bar.underMouse():
                slider_rect = self.thickness_slider.geometry()
                slider_pos = self.thickness_slider.mapToGlobal(slider_rect.topLeft())
                slider_rect_global = QRect(slider_pos, self.thickness_slider.size())
                if not slider_rect_global.contains(event.globalPos()):
                    self.dragging = True
                    self.offset = event.pos()
            elif self.drawing_label.underMouse():
                if self.bucket_mode:
                    self.bucket_fill(event.pos() - self.drawing_label.pos())
                else:
                    self.save_state_for_undo()
                    self.last_point = event.pos() - self.drawing_label.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)
        elif self.last_point is not None and event.buttons() & Qt.LeftButton:
            current_point = event.pos() - self.drawing_label.pos()
            self.draw_line(self.last_point, current_point)
            self.last_point = current_point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_point = None

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
            self.undo()
            event.accept()
            return
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_Y or event.key() == Qt.Key_Z and event.modifiers() & Qt.ShiftModifier):
            self.redo()
            event.accept()
            return
        super().keyPressEvent(event)

    def update_drawing_surface(self, event):
        if self.pixmap.size() != self.drawing_label.size():
            new_pixmap = QPixmap(self.drawing_label.size())
            new_pixmap.fill(Qt.transparent)
            
            if not self.pixmap.isNull():
                painter = QPainter(new_pixmap)
                painter.drawPixmap(0, 0, self.pixmap)
                painter.end()
            
            self.pixmap = new_pixmap
            self.drawing_label.setPixmap(self.pixmap)
        
        event.accept()
        
    def resizeEvent(self, event):
        self.update_drawing_surface(event)
        super().resizeEvent(event)
    
    def draw_line(self, from_point, to_point):
        if self.pixmap.isNull():
            return
            
        painter = QPainter(self.pixmap)
        if painter.isActive():
            if self.eraser_mode:
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                eraser_pen = QPen(Qt.transparent, self.thickness_slider.value(), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(eraser_pen)
            else:
                painter.setPen(self.pen)
            painter.drawLine(from_point, to_point)
            painter.end()
            self.drawing_label.setPixmap(self.pixmap)

    def clear_drawing(self):
        if not self.pixmap.isNull():
            self.save_state_for_undo()
            self.pixmap.fill(Qt.transparent)
            self.drawing_label.setPixmap(self.pixmap)

    def save_state_for_undo(self):
        if self.pixmap.isNull():
            return
        self.history.append(self.pixmap.copy())
        if len(self.history) > 100:
            self.history.pop(0)
        self.future.clear()
        self.update_undo_redo_buttons()

    def update_undo_redo_buttons(self):
        self.undo_button.setEnabled(len(self.history) > 0)
        self.redo_button.setEnabled(len(self.future) > 0)

    def undo(self):
        if not self.history:
            return
        self.future.append(self.pixmap.copy())
        self.pixmap = self.history.pop()
        self.drawing_label.setPixmap(self.pixmap)
        self.update_undo_redo_buttons()

    def redo(self):
        if not self.future:
            return
        self.history.append(self.pixmap.copy())
        self.pixmap = self.future.pop()
        self.drawing_label.setPixmap(self.pixmap)
        self.update_undo_redo_buttons()

    def bucket_fill(self, pos):
        self.save_state_for_undo()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            x, y = int(pos.x()), int(pos.y())
            if x < 0 or y < 0 or x >= self.pixmap.width() or y >= self.pixmap.height():
                return

            image = self.pixmap.toImage()
            target_color = image.pixelColor(x, y)

            if self.eraser_mode:
                fill_color = QColor(0, 0, 0, 0)
            else:
                fill_color = self.pen.color()

            if target_color == fill_color:
                return

            self.perform_fill(image, x, y, target_color, fill_color)
            self.pixmap.convertFromImage(image)
            self.drawing_label.setPixmap(self.pixmap)
        finally:
            QApplication.restoreOverrideCursor()

    def perform_fill(self, image, x, y, target_color, fill_color):
        width = image.width()
        height = image.height()
        stack = [(x, y)]
        visited = set()

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            if cx < 0 or cy < 0 or cx >= width or cy >= height:
                continue
            if image.pixelColor(cx, cy) != target_color:
                continue
            image.setPixelColor(cx, cy, fill_color)
            visited.add((cx, cy))
            stack.extend([
                (cx + 1, cy),
                (cx - 1, cy),
                (cx, cy + 1),
                (cx, cy - 1)
            ])


class ApplicationManager:
    @staticmethod
    def get_open_windows():
        windows = []

        def is_real_window(hwnd):
            if not win32gui.IsWindowVisible(hwnd):
                return False
            if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
                return False
            if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
                return False
            title = win32gui.GetWindowText(hwnd)
            if not title.strip():
                return False

            if "Windows Input Experience" in title or "actionOverlay" in title:
                return False

            return True

        def callback(hwnd, extra):
            if is_real_window(hwnd):
                windows.append((hwnd, win32gui.GetWindowText(hwnd)))
            return True

        win32gui.EnumWindows(callback, None)
        return windows
    
    @staticmethod
    def bring_to_current_monitor(hwnd):
        window_rect = win32gui.GetWindowRect(hwnd)
        window_width = window_rect[2] - window_rect[0]
        window_height = window_rect[3] - window_rect[1]
        
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        
        if screen:
            screen_geometry = screen.geometry()
            x = screen_geometry.x() + (screen_geometry.width() - window_width) // 2
            y = screen_geometry.y() + (screen_geometry.height() - window_height) // 2

            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, window_width, window_height, win32con.SWP_SHOWWINDOW)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.MoveWindow(hwnd, screen_geometry.x(), screen_geometry.y(), screen_geometry.width(), screen_geometry.height(), True)
    
    @staticmethod
    def close_window(hwnd):
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

class OverlayButton(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Window
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.drawing_window = None

        self.main_button = DraggableButton("○", self)
        self.main_button.clicked.connect(self.on_main_button_clicked)

        dark_button_style = """
            QPushButton {
                background-color: #2c2c2c;
                padding: 5px;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """
        self.main_button.setStyleSheet(dark_button_style)

        self.shortcuts = {
            "C": "copy",
            "V": "paste",
            "X": "cut",
            "D": "duplicate",
            "A": "select all",
            "Z": "undo",
            "Y": "redo"
        }

        self.shortcut_buttons = []
        self.shortcuts_layout = QVBoxLayout()
        self.shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        self.shortcuts_layout.setSpacing(5)
        self.shortcuts_layout.setAlignment(Qt.AlignTop)
        
        for key, name in self.shortcuts.items():
            btn = QPushButton(name, self)
            btn.setFixedSize(90, 40)
            btn.setStyleSheet(dark_button_style)
            btn.clicked.connect(lambda _, k=key: self.trigger_shortcut(k))
            btn.hide()
            self.shortcut_buttons.append(btn)
            self.shortcuts_layout.addWidget(btn)

        self.apps_button = QPushButton("apps", self)
        self.apps_button.setFixedSize(90, 40)
        self.apps_button.setStyleSheet(dark_button_style)
        self.apps_button.clicked.connect(self.toggle_apps_list)
        self.apps_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                padding: 5px;
                color: #fff;
                border: 1px solid #0d0d0d;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QPushButton:pressed {
                background-color: #595959;
            }
        """)
        self.apps_button.hide()
        self.shortcuts_layout.addWidget(self.apps_button)

        self.apps_list_layout = QVBoxLayout()
        self.apps_list_layout.setContentsMargins(0, 0, 0, 0)
        self.apps_list_layout.setSpacing(5)
        self.apps_list_layout.setAlignment(Qt.AlignTop)
        self.apps_list_widget = QWidget()
        self.apps_list_widget.setLayout(self.apps_list_layout)
        self.apps_list_widget.setFixedWidth(300)
        self.apps_list_widget.hide()

        self.print_screen_button = QPushButton("⌜⌟ print screen", self)
        self.print_screen_button.setFixedSize(90, 40)
        self.print_screen_button.setStyleSheet("""
            QPushButton {
                background-color: #286;
                padding: 5px;
                color: #fff;
                border: 1px solid #063;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #3a8;
            }
            QPushButton:pressed {
                background-color: #174;
            }
        """)
        self.print_screen_button.clicked.connect(self.take_screenshot)
        self.print_screen_button.hide()
        self.shortcuts_layout.addWidget(self.print_screen_button)

        self.draw_button = QPushButton("✎ draw", self)
        self.draw_button.setFixedSize(90, 40)
        self.draw_button.setStyleSheet("""
            QPushButton {
                background-color: #228;
                padding: 5px;
                color: #fff;
                border: 1px solid #006;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #33a;
            }
            QPushButton:pressed {
                background-color: #116;
            }
        """)
        self.draw_button.clicked.connect(self.toggle_drawing_window)
        self.draw_button.hide()
        self.shortcuts_layout.addWidget(self.draw_button)

        self.quit_button = QPushButton("✖ quit", self)
        self.quit_button.setFixedSize(90, 40)
        self.quit_button.setStyleSheet("""
            QPushButton {
                background-color: #922;
                padding: 5px;
                color: #fff;
                border: 1px solid #600;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #b33;
            }
            QPushButton:pressed {
                background-color: #811;
            }
        """)
        self.quit_button.clicked.connect(QApplication.quit)
        self.quit_button.hide()
        self.shortcuts_layout.addWidget(self.quit_button)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        main_button_container = QWidget()
        main_button_layout = QVBoxLayout(main_button_container)
        main_button_layout.setContentsMargins(0, 0, 0, 0)
        main_button_layout.addWidget(self.main_button, 0, Qt.AlignTop)
        main_button_layout.addStretch()

        main_layout.addWidget(main_button_container)
        main_layout.addLayout(self.shortcuts_layout)
        main_layout.addWidget(self.apps_list_widget)

        self._resize_timer = QTimer(self)
        self._resize_timer.timeout.connect(self.adjustSize)
        self._resize_timer.start(50)

    def take_screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')

    def toggle_buttons(self):
        visible = self.shortcut_buttons[0].isVisible()
        for btn in self.shortcut_buttons:
            btn.setVisible(not visible)
        self.print_screen_button.setVisible(not visible)
        self.draw_button.setVisible(not visible)
        self.quit_button.setVisible(not visible)
        self.apps_button.setVisible(not visible)
        self.main_button.setText("○" if visible else "◌")
        
        if visible:
            self.apps_list_widget.hide()
        self.adjustSize()

    def toggle_apps_list(self):
        if self.apps_list_widget.isVisible():
            self.apps_list_widget.hide()
        else:
            self.populate_apps_list()
            self.apps_list_widget.show()
        self.adjustSize()

    def populate_apps_list(self):
        for i in reversed(range(self.apps_list_layout.count())): 
            widget = self.apps_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
            else:
                layout = self.apps_list_layout.itemAt(i).layout()
                if layout:
                    for j in reversed(range(layout.count())):
                        layout.itemAt(j).widget().setParent(None)
                    self.apps_list_layout.removeItem(layout)
        
        windows = ApplicationManager.get_open_windows()
        
        for hwnd, title in windows[:15]:
            window_layout = QHBoxLayout()
            window_layout.setSpacing(5)
            
            short_title = title[:30] + "..." if len(title) > 30 else title
            label = QLabel(short_title)
            label.setStyleSheet("""
                background-color: #222;
                border-radius: 8px;
                padding: 2px 6px;
                border: 1px solid #444;
                color: white;
            """)
            label.setFixedSize(180, 40)
            window_layout.addWidget(label)
            
            if "Task Manager" not in title:
                bring_btn = QPushButton("⇲")
                bring_btn.setFixedSize(40, 40)
                bring_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #286;
                        color: white;
                        border: none;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #3a8;
                    }
                """)
                bring_btn.clicked.connect(lambda _, h=hwnd: (ApplicationManager.bring_to_current_monitor(h), self.toggle_apps_list()))
                window_layout.addWidget(bring_btn)

            
            if "Task Manager" not in title:
                close_btn = QPushButton("✕")
                close_btn.setFixedSize(40, 40)
                close_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #922;
                        color: white;
                        border: none;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #b33;
                    }
                """)

                def bring_and_close(h):
                    ApplicationManager.bring_to_current_monitor(h)
                    QTimer.singleShot(300, lambda: ApplicationManager.close_window(h))
                    self.toggle_apps_list()
                close_btn.clicked.connect(lambda _, h=hwnd: bring_and_close(h))
                window_layout.addWidget(close_btn)
            else:
                disabled_btn = QPushButton("No permission")
                disabled_btn.setFixedSize(110, 40)
                disabled_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2c2c2c;
                        padding: 0px;
                        color: #807d7d;
                        border: 1px solid #444;
                        border-radius: 10px;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #2c2c2c;
                    }
                """)
                window_layout.addWidget(disabled_btn)
            
            self.apps_list_layout.addLayout(window_layout)
        self.adjustSize()

    def trigger_shortcut(self, key):
        pyautogui.keyDown('alt')
        pyautogui.press('tab')
        pyautogui.keyUp('alt')
        pyautogui.sleep(0.1)
        pyautogui.hotkey('ctrl', key.lower())

    def on_main_button_clicked(self):
        if not self.main_button.was_dragging:
            self.toggle_buttons()

    def toggle_drawing_window(self):
        if self.drawing_window is None or not self.drawing_window.isVisible():
            self.drawing_window = DrawingWindow()
            
            cursor_pos = QCursor.pos()
            screen = QApplication.screenAt(cursor_pos)
            if screen:
                screen_geometry = screen.availableGeometry()
                window_width = min(800, screen_geometry.width() - 100)
                window_height = min(600, screen_geometry.height() - 100)
                x = screen_geometry.x() + (screen_geometry.width() - window_width) // 2
                y = screen_geometry.y() + (screen_geometry.height() - window_height) // 2
                self.drawing_window.setGeometry(x, y, window_width, window_height)
            
            self.drawing_window.show()
            self.draw_button.setStyleSheet("""
                QPushButton {
                    background-color: #44a;
                    padding: 5px;
                    color: #fff;
                    border: 1px solid #006;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #55b;
                }
                QPushButton:pressed {
                    background-color: #338;
                }
            """)
        else:
            self.drawing_window.close()
            self.draw_button.setStyleSheet("""
                QPushButton {
                    background-color: #228;
                    padding: 5px;
                    color: #fff;
                    border: 1px solid #006;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #33a;
                }
                QPushButton:pressed {
                    background-color: #116;
                }
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayButton()
    overlay.show()
    sys.exit(app.exec_())