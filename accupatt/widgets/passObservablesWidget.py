import accupatt.config as cfg
from accupatt.models.passData import Pass
from accupatt.models.passTable import FILLER_HIDDEN_ROWS, ComboBoxDelegate, PassTable
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication, QHeaderView, QPushButton, QTableView, QVBoxLayout, QWidget
# Minimum acceptable column width (px) before switching to scroll mode
_MIN_COL_WIDTH = 70


_GROUND_SPEED_ROW = 5  # row index of Ground Speed in PassTable


class _PassObsTableView(QTableView):
    """QTableView that jumps to Pass 1 Ground Speed when focused via keyboard Tab."""
    def focusInEvent(self, event):
        super().focusInEvent(event)
        if (
            event.reason() == Qt.FocusReason.TabFocusReason
            and self.model()
            and self.model().columnCount() > 0
        ):
            idx = self.model().index(_GROUND_SPEED_ROW, 0)
            self.setCurrentIndex(idx)


class _ObservablesPassTable(PassTable):
    """PassTable variant: blanks the Name row header; data rows have white background."""
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if section == 0 and orientation == Qt.Orientation.Vertical:
            return None
        return super().headerData(section, orientation, role)

    def data(self, index, role):
        if role == Qt.ItemDataRole.BackgroundRole and index.row() != 0:
            return QApplication.palette().color(QPalette.ColorRole.Base)
        return super().data(index, role)

    def flags(self, index):
        if index.row() == 0:
            return Qt.ItemFlag.ItemIsEnabled
        return super().flags(index)


class PassObservablesWidget(QWidget):
    request_open_pass_manager = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table_view = _PassObsTableView()
        self._table_view.setFrameShape(QTableView.Shape.NoFrame)
        self._table_view.horizontalHeader().setVisible(False)
        self._table_view.horizontalHeader().setMinimumSectionSize(_MIN_COL_WIDTH)
        self._table_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._table_view.viewport().setAutoFillBackground(False)
        self._table_view.setStyleSheet(
            "QHeaderView::section { background: transparent; border: none; }"
            " QHeaderView { background: transparent; }"
        )
        layout.addWidget(self._table_view)

        self._btn_manage = QPushButton("Manage Passes...")
        self._btn_manage.clicked.connect(self.request_open_pass_manager)
        layout.addWidget(self._btn_manage)

        self._model: _ObservablesPassTable | None = None

    def set_pass_list(self, pass_list: list[Pass]):
        self._model = _ObservablesPassTable(pass_list, parent=self, filler_mode=True)
        self._table_view.setModel(self._model)
        for row, units in [
            (6, cfg.UNITS_GROUND_SPEED),
            (8, cfg.UNITS_SPRAY_HEIGHT),
            (12, cfg.UNITS_WIND_SPEED),
            (14, cfg.UNITS_TEMPERATURE),
        ]:
            self._table_view.setItemDelegateForRow(row, ComboBoxDelegate(self, units))
        self._apply_filler_rows()
        self._apply_column_mode()
        QTimer.singleShot(0, self._fit_height)

    def refresh(self):
        if self._model is None:
            return
        self._model.beginResetModel()
        self._model.endResetModel()
        # QTableView loses hideRow state on model reset — must reapply
        self._apply_filler_rows()
        self._apply_column_mode()
        QTimer.singleShot(0, self._fit_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_column_mode()
        self._fit_height()

    def _apply_filler_rows(self):
        for row in FILLER_HIDDEN_ROWS:
            self._table_view.hideRow(row)

    def _fit_height(self):
        """Fix the table height to exactly its visible row content."""
        tv = self._table_view
        if tv.model() is None:
            return
        vh = tv.verticalHeader()
        h = tv.frameWidth() * 2
        for row in range(tv.model().rowCount()):
            if not tv.isRowHidden(row):
                row_h = vh.sectionSize(row)
                h += row_h if row_h > 0 else vh.defaultSectionSize()
        if tv.horizontalScrollBar().isVisible():
            h += tv.horizontalScrollBar().sizeHint().height()
        tv.setFixedHeight(h)

    def _apply_column_mode(self):
        if self._model is None:
            return
        n = self._model.columnCount()
        if n == 0:
            return
        available = self._table_view.viewport().width()
        header = self._table_view.horizontalHeader()
        if available >= n * _MIN_COL_WIDTH:
            # Enough room — stretch columns to fill the full width
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        else:
            # Too many passes to fit — let each column be its natural width
            # and allow the horizontal scrollbar to appear
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
