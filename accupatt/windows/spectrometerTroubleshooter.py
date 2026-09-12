"""Operator-facing spectrometer troubleshooter.

Shown when Test Spectrometer is pressed and no working spectrometer is
available. It says what is wrong, what to try, and lets the operator rescan
without leaving the dialog -- the usual sequence is "reseat the cable, try
again", and making that one click is most of the value.

The technical report is collapsed by default and copyable, so a stuck user can
send AccuPatt support something useful instead of "it doesn't work".
"""

from accupatt.hardware import diagnostics

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
)

_STATUS_COLORS = {
    diagnostics.OK: "#1b7f3b",
    diagnostics.NO_DEVICE: "#a86b00",
    diagnostics.OPEN_FAILED: "#a86b00",
    diagnostics.DEVICE_ERROR: "#a83232",
    diagnostics.NO_DRIVER: "#a83232",
    diagnostics.DRIVER_LOAD_FAILED: "#a83232",
}


class SpectrometerTroubleshooter(QDialog):
    """Returns Accepted when the operator wants to go on to the live view."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Spectrometer Troubleshooter")
        self._CONTENT_WIDTH = 520
        self.diagnosis: diagnostics.Diagnosis | None = None

        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.lbl_headline = QLabel()
        self.lbl_headline.setWordWrap(True)
        self.lbl_headline.setMinimumWidth(self._CONTENT_WIDTH)
        self.lbl_headline.setStyleSheet("font-size: 15pt; font-weight: 600;")
        layout.addWidget(self.lbl_headline)

        self.lbl_explanation = QLabel()
        self.lbl_explanation.setWordWrap(True)
        self.lbl_explanation.setMinimumWidth(self._CONTENT_WIDTH)
        self.lbl_explanation.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        layout.addWidget(self.lbl_explanation)

        self.lbl_steps = QLabel()
        self.lbl_steps.setWordWrap(True)
        self.lbl_steps.setMinimumWidth(self._CONTENT_WIDTH)
        self.lbl_steps.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        self.lbl_steps.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.lbl_steps)

        # Technical report: present but out of the way until asked for.
        self.btn_details = QToolButton()
        self.btn_details.setText("Technical details")
        self.btn_details.setCheckable(True)
        self.btn_details.setStyleSheet("border: none;")
        self.btn_details.setArrowType(Qt.ArrowType.RightArrow)
        self.btn_details.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_details.toggled.connect(self._toggle_details)
        row = QHBoxLayout()
        row.addWidget(self.btn_details)
        row.addStretch()
        layout.addLayout(row)

        self.txt_details = QPlainTextEdit()
        self.txt_details.setReadOnly(True)
        self.txt_details.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.txt_details.setMaximumHeight(190)
        self.txt_details.hide()
        layout.addWidget(self.txt_details)

        buttons = QDialogButtonBox(self)
        self.btn_rescan: QPushButton = buttons.addButton(
            "Rescan", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.btn_copy: QPushButton = buttons.addButton(
            "Copy Details", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.btn_live: QPushButton = buttons.addButton(
            "Open Live View", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.btn_close: QPushButton = buttons.addButton(
            "Close", QDialogButtonBox.ButtonRole.RejectRole
        )
        self.btn_rescan.clicked.connect(self.rescan)
        self.btn_copy.clicked.connect(self._copy)
        self.btn_live.clicked.connect(self.accept)
        self.btn_close.clicked.connect(self.reject)
        layout.addWidget(buttons)

        self.rescan()

    def _toggle_details(self, shown: bool):
        self.btn_details.setArrowType(
            Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow
        )
        self.txt_details.setVisible(shown)

    def rescan(self):
        """Re-run the probe and repaint. Safe to call repeatedly."""
        self.btn_rescan.setEnabled(False)
        self.btn_rescan.setText("Scanning…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            self.diagnosis = diagnostics.diagnose()
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_rescan.setEnabled(True)
            self.btn_rescan.setText("Rescan")
        self._render()

    def _render(self):
        d = self.diagnosis
        color = _STATUS_COLORS.get(d.status, "#a86b00")
        self.lbl_headline.setText(d.headline)
        self.lbl_headline.setStyleSheet(
            f"font-size: 15pt; font-weight: 600; color: {color};"
        )
        self.lbl_explanation.setText(d.explanation)

        if d.steps:
            items = "".join(f"<li style='margin-bottom:4px;'>{s}</li>" for s in d.steps)
            self.lbl_steps.setText(f"<b>Try this:</b><ol>{items}</ol>")
            self.lbl_steps.show()
        else:
            self.lbl_steps.hide()

        self.txt_details.setPlainText(d.as_report())

        # Only offer the live view once there is something to look at.
        self.btn_live.setVisible(d.ok)
        self.btn_live.setDefault(d.ok)
        self.btn_close.setText("Close" if d.ok else "Cancel")

    def _copy(self):
        QGuiApplication.clipboard().setText(self.diagnosis.as_report())
        self.btn_copy.setText("Copied")
        self.btn_copy.setEnabled(False)

        def restore():
            self.btn_copy.setText("Copy Details")
            self.btn_copy.setEnabled(True)

        QTimer.singleShot(1500, restore)
