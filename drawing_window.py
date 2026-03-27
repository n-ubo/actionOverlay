import pyautogui
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, QObject, QTimer
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, 
                            QSlider, QFileDialog, QApplication)
from PyQt5.QtGui import (QCursor, QFont, QPainter, QPen, QColor, QPixmap, 
                         QMouseEvent, QIcon, QImage)


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

        self.active_image = None
        self.active_image_original = None
        self.active_image_pos = QPoint(0, 0)
        self.active_image_rect = QRect()
        self.active_image_dragging = False
        self.active_image_resizing = False
        self.active_image_resize_handle = None
        self.active_image_drag_offset = QPoint(0, 0)
        self.current_mouse_pos = QPoint(0, 0)
        self.active_image_current_size = QSize()

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
                click_pos = event.pos() - self.drawing_label.pos()
                if self.active_image is not None and not self.active_image_rect.isNull():
                    # Create expanded detection rect to include handle areas
                    detection_half = 20  # Half of detection_size
                    detection_rect = self.active_image_rect.adjusted(-detection_half, -detection_half, detection_half, detection_half)
                    
                    if detection_rect.contains(click_pos):
                        handle = self.get_active_image_handle(click_pos)
                        if handle:
                            self.active_image_resizing = True
                            self.active_image_resize_handle = handle
                        else:
                            self.active_image_dragging = True
                            self.active_image_drag_offset = click_pos - self.active_image_pos
                        return
                    else:
                        self.commit_active_image()
                        return

                if self.bucket_mode:
                    self.bucket_fill(click_pos)
                else:
                    self.save_state_for_undo()
                    self.last_point = click_pos

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)
            return

        cursor_pos = event.pos() - self.drawing_label.pos()
        self.current_mouse_pos = cursor_pos

        if not (event.buttons() & Qt.LeftButton):
            self.update_cursor_for_position(cursor_pos)
            self.update_canvas_display()

        if self.active_image is not None and event.buttons() & Qt.LeftButton:
            if self.active_image_resizing and self.active_image_resize_handle and self.active_image_original is not None:
                rect = self.active_image_rect
                fixed = QPoint()

                if self.active_image_resize_handle == 'br':
                    fixed = rect.topLeft()
                elif self.active_image_resize_handle == 'bm':
                    fixed = rect.topLeft()
                elif self.active_image_resize_handle == 'rm':
                    fixed = rect.topLeft()

                width = max(20, abs(cursor_pos.x() - fixed.x()))
                height = max(20, abs(cursor_pos.y() - fixed.y()))

                if self.active_image_resize_handle == 'bm':
                    # Vertical stretch: keep width, change height
                    width = rect.width()
                elif self.active_image_resize_handle == 'rm':
                    # Horizontal stretch: keep height, change width
                    height = rect.height()

                new_size = self.active_image_current_size
                new_size.scale(width, height, Qt.KeepAspectRatio if self.active_image_resize_handle == 'br' else Qt.IgnoreAspectRatio)

                scaled = self.active_image_original.scaled(new_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                if not scaled.isNull():
                    self.active_image = scaled
                    new_w = scaled.width()
                    new_h = scaled.height()

                    if self.active_image_resize_handle == 'br':
                        self.active_image_pos = fixed
                    elif self.active_image_resize_handle == 'bm':
                        self.active_image_pos = QPoint(rect.left(), fixed.y())
                    elif self.active_image_resize_handle == 'rm':
                        self.active_image_pos = QPoint(fixed.x(), rect.top())

                    self.update_active_image_rect()
                    self.update_canvas_display()
                return

            if self.active_image_dragging:
                self.active_image_pos = cursor_pos - self.active_image_drag_offset
                self.update_active_image_rect()
                self.update_canvas_display()
                return

        if self.last_point is not None and event.buttons() & Qt.LeftButton and not self.active_image:
            current_point = cursor_pos
            self.draw_line(self.last_point, current_point)
            self.last_point = current_point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_point = None
            if self.active_image_dragging:
                self.active_image_dragging = False
            if self.active_image_resizing:
                self.active_image_resizing = False
                self.active_image_resize_handle = None
                # Update current size after resize completes
                if self.active_image is not None:
                    self.active_image_current_size = self.active_image.size()

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self.undo()
                event.accept()
                return
            if event.key() == Qt.Key_Y or (event.key() == Qt.Key_Z and event.modifiers() & Qt.ShiftModifier):
                self.redo()
                event.accept()
                return
            if event.key() == Qt.Key_V:
                clipboard = QApplication.clipboard()
                if clipboard.mimeData().hasImage():
                    image = clipboard.pixmap()
                    if not image.isNull():
                        self.set_active_image(image)
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

        self.update_canvas_display()
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
            self.update_canvas_display()

    def clear_drawing(self):
        if not self.pixmap.isNull():
            self.save_state_for_undo()
            self.pixmap.fill(Qt.transparent)
            self.active_image = None
            self.active_image_original = None
            self.active_image_rect = QRect()
            self.active_image_dragging = False
            self.active_image_resizing = False
            self.active_image_resize_handle = None
            self.update_canvas_display()

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
        self.update_canvas_display()
        self.update_undo_redo_buttons()

    def get_display_pixmap(self):
        display = self.pixmap.copy()
        if self.active_image is not None and not self.active_image.isNull():
            painter = QPainter(display)
            if painter.isActive():
                painter.drawPixmap(self.active_image_pos, self.active_image)

                # Determine colors based on mouse position
                mouse_inside = self.active_image_rect.contains(self.current_mouse_pos)
                outline_color = QColor(0, 122, 255) if mouse_inside else QColor(255, 255, 255)  # Blue if inside, white otherwise
                handle_color = outline_color

                pen = QPen(outline_color, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(self.active_image_rect)

                handle_size = 16
                handle_half = handle_size // 2

                # Bottom-right handle
                br = self.active_image_rect.bottomRight()
                br_rect = QRect(br.x() - handle_half, br.y() - handle_half, handle_size, handle_size)
                hover_br = br_rect.contains(self.current_mouse_pos)
                painter.fillRect(br_rect, handle_color if not hover_br else QColor(0, 100, 200))  # Darker blue on hover

                # Bottom-middle handle (vertical stretch)
                bm = QPoint(self.active_image_rect.center().x(), self.active_image_rect.bottom())
                bm_rect = QRect(bm.x() - handle_half, bm.y() - handle_half, handle_size, handle_size)
                hover_bm = bm_rect.contains(self.current_mouse_pos)
                painter.fillRect(bm_rect, handle_color if not hover_bm else QColor(0, 100, 200))

                # Right-middle handle (horizontal stretch)
                rm = QPoint(self.active_image_rect.right(), self.active_image_rect.center().y())
                rm_rect = QRect(rm.x() - handle_half, rm.y() - handle_half, handle_size, handle_size)
                hover_rm = rm_rect.contains(self.current_mouse_pos)
                painter.fillRect(rm_rect, handle_color if not hover_rm else QColor(0, 100, 200))

            painter.end()
        return display

    def update_canvas_display(self):
        self.drawing_label.setPixmap(self.get_display_pixmap())

    def update_active_image_rect(self):
        if self.active_image is not None:
            self.active_image_rect = QRect(self.active_image_pos, self.active_image.size())

    def set_active_image(self, pixmap):
        if pixmap is None or pixmap.isNull():
            return
        self.active_image_original = pixmap
        self.active_image = pixmap.copy()
        self.active_image_current_size = pixmap.size()
        self.active_image_pos = QPoint(
            max(0, (self.drawing_label.width() - self.active_image.width()) // 2),
            max(0, (self.drawing_label.height() - self.active_image.height()) // 2)
        )
        self.update_active_image_rect()
        self.update_canvas_display()

    def commit_active_image(self):
        if self.active_image is None:
            return
        self.save_state_for_undo()
        painter = QPainter(self.pixmap)
        if painter.isActive():
            painter.drawPixmap(self.active_image_pos, self.active_image)
            painter.end()
        self.active_image = None
        self.active_image_original = None
        self.active_image_rect = QRect()
        self.active_image_dragging = False
        self.active_image_resizing = False
        self.active_image_resize_handle = None
        self.update_canvas_display()

    def get_active_image_handle(self, pos):
        if self.active_image_rect.isNull():
            return None
        handle_size = 16  # Display size
        detection_size = 40  # Even larger for easier clicking
        detection_half = detection_size // 2

        # Bottom-right handle
        br = self.active_image_rect.bottomRight()
        br_rect = QRect(br.x() - detection_half, br.y() - detection_half, detection_size, detection_size)
        if br_rect.contains(pos):
            return 'br'

        # Bottom-middle handle (vertical stretch)
        bm = QPoint(self.active_image_rect.center().x(), self.active_image_rect.bottom())
        bm_rect = QRect(bm.x() - detection_half, bm.y() - detection_half, detection_size, detection_size)
        if bm_rect.contains(pos):
            return 'bm'

        # Right-middle handle (horizontal stretch)
        rm = QPoint(self.active_image_rect.right(), self.active_image_rect.center().y())
        rm_rect = QRect(rm.x() - detection_half, rm.y() - detection_half, detection_size, detection_size)
        if rm_rect.contains(pos):
            return 'rm'

        return None

    def update_cursor_for_position(self, pos):
        if self.active_image is not None and not self.active_image_rect.isNull():
            handle = self.get_active_image_handle(pos)
            if handle == 'br':
                self.setCursor(Qt.SizeFDiagCursor)
                return
            if self.active_image_rect.contains(pos):
                self.setCursor(Qt.SizeAllCursor)
                return
        self.setCursor(Qt.ArrowCursor)

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
            self.update_canvas_display()
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
