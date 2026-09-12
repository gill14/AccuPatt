import sys

import accupatt.config as cfg

from PyQt6.QtWidgets import QApplication

from accupatt.windows.eula import require_acceptance
from accupatt.windows.mainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOrganizationName("mattgill")
    app.setApplicationDisplayName("AccuPatt")
    app.setApplicationName("accupatt")
    app.setApplicationVersion(cfg.get_version_string())
    # Required by the OceanDirect API Terms (1.2(b)): the user accepts the
    # AccuPatt EULA before reaching the application.
    if not require_acceptance():
        sys.exit(0)
    w = MainWindow()
    sys.exit(app.exec())
