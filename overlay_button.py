import pyautogui
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QApplication)

from buttons import DraggableButton
from application_manager import ApplicationManager
from drawing_window import DrawingWindow


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
            
            from PyQt5.QtGui import QCursor
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
