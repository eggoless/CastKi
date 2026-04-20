from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

VERSION = "1.0.0"
REPO_URL = "https://github.com/eggoless/CastKi"


class SettingsDialog(QDialog):
    def __init__(self, saves_dir: Path, default_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(440)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._path = saves_dir
        self._default_dir = default_dir
        self._reset_all = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel("Save folder for screenshots and recordings:"))

        row = QHBoxLayout()
        self._path_edit = QLineEdit(str(saves_dir))
        self._path_edit.setReadOnly(True)
        row.addWidget(self._path_edit, stretch=1)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #444;")
        layout.addWidget(sep)

        about = QLabel(
            f"<span style='font-size:13px;font-weight:600;'>CastKi v{VERSION}</span><br>"
            f"<span style='color:#909090;'>Created by Eggoless &nbsp;·&nbsp; "
            f"<a href='{REPO_URL}' style='color:#00c896;'>{REPO_URL}</a></span>"
        )
        about.setTextFormat(Qt.TextFormat.RichText)
        about.setOpenExternalLinks(True)
        layout.addWidget(about)

        btn_row = QHBoxLayout()
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        btn_row.addWidget(buttons)
        layout.addLayout(btn_row)

    def _browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Select save folder", str(self._path))
        if chosen:
            self._path = Path(chosen)
            self._path_edit.setText(chosen)

    def _reset_defaults(self) -> None:
        self._path = self._default_dir
        self._path_edit.setText(str(self._default_dir))
        self._reset_all = True

    @property
    def saves_dir(self) -> Path:
        return self._path

    @property
    def reset_all(self) -> bool:
        return self._reset_all
