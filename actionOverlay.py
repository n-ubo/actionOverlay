import sys
from PyQt5.QtWidgets import QApplication

from overlay_button import OverlayButton


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayButton()
    overlay.show()
    sys.exit(app.exec_())
