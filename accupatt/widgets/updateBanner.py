"""Dismissible status-bar banner notifying that a newer AccuPatt release exists."""

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

import accupatt.config as cfg

_PILL_STYLE = "background-color: #FFD700; border-radius: 8px; padding: 3px 10px; color: black;"


class UpdateBanner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._html_url = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QLabel(self)
        self._label.setStyleSheet(_PILL_STYLE)
        self._label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._label.mousePressEvent = lambda event: self._open_release()
        layout.addWidget(self._label)

        dismiss = QPushButton("✕", self)
        dismiss.setFlat(True)
        dismiss.setFixedWidth(18)
        dismiss.setStyleSheet(_PILL_STYLE)
        dismiss.setToolTip("Dismiss")
        dismiss.clicked.connect(self._dismiss)
        layout.addWidget(dismiss)

        self.hide()

    def show_update(self, version: str, html_url: str):
        self._version = version
        self._html_url = html_url
        self._label.setText(f"AccuPatt {version} is available")
        self.show()

    def _open_release(self):
        if self._html_url:
            QDesktopServices.openUrl(QUrl(self._html_url))

    def _dismiss(self):
        cfg.set_update_dismissed_version(self._version)
        self.hide()
