# -*- coding: utf-8 -*-
import sys
import logging
from PyQt6 import QtWidgets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    from ui.main_window import MainWindow
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("ColorIQ")
    app.setOrganizationName("ColorIQ")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
