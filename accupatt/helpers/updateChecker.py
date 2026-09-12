"""Background check for a newer AccuPatt release on GitHub.

Runs on its own QThread so a slow or absent network connection never delays
app startup. Failures of any kind (offline, GitHub unreachable, unexpected
response shape) are swallowed silently -- this is a courtesy notification,
never something that should interrupt or alarm the user.
"""

import json
import urllib.request

from PyQt6.QtCore import QObject, pyqtSignal

import accupatt.config as cfg

_RELEASES_URL = "https://api.github.com/repos/gill14/AccuPatt/releases/latest"
_TIMEOUT_SECONDS = 5


def _version_tuple(version: str) -> tuple:
    """Parse "2.10.0" -> (2, 10, 0). Numeric comparison, not lexicographic --
    "2.9.0" must sort below "2.10.0"."""
    parts = []
    for piece in version.split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            break
    return tuple(parts)


def is_newer(candidate: str, current: str) -> bool:
    return _version_tuple(candidate) > _version_tuple(current)


class UpdateCheckWorker(QObject):
    update_available = pyqtSignal(str, str)  # version, html_url
    finished = pyqtSignal()

    def run(self):
        try:
            with urllib.request.urlopen(_RELEASES_URL, timeout=_TIMEOUT_SECONDS) as resp:
                data = json.load(resp)
            latest = str(data["tag_name"]).lstrip("v")
            html_url = str(data["html_url"])
            if is_newer(latest, cfg.get_version_string()) and latest != cfg.get_update_dismissed_version():
                self.update_available.emit(latest, html_url)
        except Exception:
            pass
        finally:
            self.finished.emit()
