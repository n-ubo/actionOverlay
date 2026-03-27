import win32gui
import win32con
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCursor


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
