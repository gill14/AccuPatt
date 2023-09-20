import sys

import accupatt.config as cfg

from PyQt6.QtWidgets import QApplication

import seabreeze
seabreeze.use('pyseabreeze', force=False)

from accupatt.windows.mainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOrganizationName("mattgill")
    app.setApplicationDisplayName("AccuPatt")
    app.setApplicationName("accupatt")
    app.setApplicationVersion(
        f"{str(cfg.VERSION_MAJOR)}.{str(cfg.VERSION_MINOR)}.{str(cfg.VERSION_RELEASE)}"
    )
    w = MainWindow()
    sys.exit(app.exec())
