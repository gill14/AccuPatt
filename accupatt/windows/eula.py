"""First-run license acceptance.

The OceanDirect API Terms (1.2(b)) let AccuPatt redistribute the OceanDirect
runtime only under a written EULA that the user accepts *before* accessing the
application. The Windows installer shows the same document, but a user can
arrive without ever seeing it -- copying AccuPatt.app out of the DMG, restoring
from a backup, or running from source -- so the gate lives here too, in front
of MainWindow.
"""

import accupatt.config as cfg

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)


class EulaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("AccuPatt License Agreement")
        self.setMinimumSize(720, 560)

        layout = QVBoxLayout(self)

        heading = QLabel(
            "Please read and accept the AccuPatt End User License Agreement "
            "to continue."
        )
        heading.setWordWrap(True)
        layout.addWidget(heading)

        self.text = QPlainTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setPlainText(self._load_text())
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text)

        note = QLabel(
            "AccuPatt includes the OceanDirect SDK, licensed from Ocean Optics, "
            "Inc. Section 2 of this agreement restricts how that component may "
            "be used."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #666666;")
        layout.addWidget(note)

        buttons = QDialogButtonBox(self)
        self.btn_accept = buttons.addButton(
            "I Accept", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.btn_decline = buttons.addButton(
            "Decline and Quit", QDialogButtonBox.ButtonRole.RejectRole
        )
        self.btn_accept.clicked.connect(self.accept)
        self.btn_decline.clicked.connect(self.reject)
        layout.addWidget(buttons)

        # Nothing here should be dismissible by Esc or the title-bar close box:
        # both would read as acceptance without one.
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

    def _load_text(self) -> str:
        try:
            with open(cfg.get_eula_path(), encoding="utf-8") as f:
                return f.read()
        except OSError:
            # Never fail open. If the document is missing, the honest outcome
            # is to say so rather than let the user past an empty box.
            return (
                "The AccuPatt End User License Agreement could not be loaded.\n\n"
                "This installation may be incomplete. Please reinstall "
                "AccuPatt, or obtain the agreement from\n"
                "https://github.com/gill14/AccuPatt"
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)

    def reject(self):
        confirm = QMessageBox.question(
            self,
            "Decline License Agreement",
            "AccuPatt cannot run unless you accept the license agreement.\n\n"
            "Quit AccuPatt?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            super().reject()


def require_acceptance(parent=None) -> bool:
    """Show the EULA if this version has not been accepted yet.

    Returns True when AccuPatt may start.
    """
    if cfg.is_eula_accepted():
        return True
    if EulaDialog(parent=parent).exec() == QDialog.DialogCode.Accepted:
        cfg.set_eula_accepted_version(cfg.EULA_VERSION)
        return True
    return False
