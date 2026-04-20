from __future__ import annotations

import datetime
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, QSettings, QTimer, QUrl, Signal
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import (
    QAudioInput, QCamera, QCameraDevice, QImageCapture,
    QMediaCaptureSession, QMediaDevices, QMediaFormat, QMediaRecorder,
    QVideoFrame, QVideoSink,
)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QPushButton, QSizePolicy, QSlider, QVBoxLayout, QWidget,
)

from ui.settings_dialog import SettingsDialog
from utils.audio import AudioPassthrough
from utils.devices import format_label, get_shadowcast_device, list_formats
from utils.virtualcam import VirtualCamPublisher


_DEFAULT_SAVES_DIR = Path.home() / "Videos" / "Castki"

BAR_TOP      = "#464646"
BAR_BG       = "#3d3d3d"
TEXT_PRIMARY = "#efefef"
TEXT_DIM     = "#909090"
ACCENT       = "#00c896"
BADGE_GREY   = "#5a5a5a"
BADGE_RED    = "#c62828"
BADGE_BLUE   = "#3a7abf"
BADGE_GREEN  = "#2e7d52"
BADGE_PURPLE = "#7b3fb5"

APP_STYLE = f"""
* {{
    font-family: 'Segoe UI', Arial, sans-serif;
    color: {TEXT_PRIMARY};
    background: transparent;
}}
QMainWindow {{ background: #0d0d0d; }}
#videoRoot   {{ background: #0d0d0d; }}
QVideoWidget {{ background: #000000; }}
#controlBar {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 {BAR_TOP}, stop:1 {BAR_BG});
    border-top: 1px solid #585858;
}}
QComboBox {{
    background: rgba(0,0,0,0.20); color: {TEXT_PRIMARY};
    border: 1px solid #5e5e5e; border-radius: 14px;
    padding: 5px 14px; font-size: 13px; min-width: 175px;
}}
QComboBox:hover {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 16px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_DIM}; width: 0; height: 0; margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: #2e2e2e; color: {TEXT_PRIMARY}; border: 1px solid #555;
    selection-background-color: {ACCENT}; selection-color: #0d0d0d;
    outline: none; padding: 2px;
}}
QSlider {{ background: transparent; }}
QSlider::groove:horizontal {{
    height: 3px; background: rgba(255,255,255,0.18); border-radius: 2px;
}}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    width: 13px; height: 13px; margin: -5px 0;
    background: {TEXT_PRIMARY}; border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{ background: {ACCENT}; }}
#vdiv {{ background: #5a5a5a; max-width: 1px; min-width: 1px; }}
#volPct      {{ color: {TEXT_DIM}; font-size: 12px; min-width: 32px; }}
#statusLabel {{ color: {TEXT_DIM}; font-size: 12px; }}
#deviceBtn {{
    background: rgba(0,0,0,0.15); color: {TEXT_DIM};
    border: 1px solid #585858; border-radius: 14px;
    padding: 5px 14px; font-size: 12px; text-align: left;
}}
#deviceBtn:hover {{
    background: rgba(0,0,0,0.28); color: {TEXT_PRIMARY}; border-color: #787878;
}}
#gearBtn {{
    background: rgba(15,15,15,0.72);
    color: #ffffff;
    border: 1.5px solid rgba(255,255,255,0.30);
    border-radius: 20px;
    font-size: 20px;
    padding: 0;
}}
#gearBtn:hover {{
    background: rgba(50,50,50,0.88);
    border-color: rgba(255,255,255,0.55);
}}
QMenu {{
    background: #2a2a2a; color: {TEXT_PRIMARY};
    border: 1px solid #555; padding: 4px;
}}
QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
QMenu::item:selected {{ background: {ACCENT}; color: #0d0d0d; }}
QMenu::item:checked {{ font-weight: 600; }}
QDialog {{
    background: #1e1e1e;
}}
QDialog QLabel {{
    color: {TEXT_PRIMARY}; font-size: 13px;
}}
QDialog QLineEdit {{
    background: rgba(0,0,0,0.30); color: {TEXT_PRIMARY};
    border: 1px solid #5e5e5e; border-radius: 6px;
    padding: 5px 10px; font-size: 13px;
}}
QDialog QPushButton {{
    background: rgba(0,0,0,0.20); color: {TEXT_PRIMARY};
    border: 1px solid #5e5e5e; border-radius: 6px;
    padding: 5px 16px; font-size: 13px; min-width: 80px;
}}
QDialog QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QDialogButtonBox QPushButton {{ min-width: 80px; }}
"""


# ── Video area ────────────────────────────────────────────────────────────────

class VideoArea(QWidget):
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._video = QVideoWidget(self)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def video_widget(self) -> QVideoWidget:
        return self._video

    def resizeEvent(self, event) -> None:
        self._video.setGeometry(self.rect())

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ── Action hint ───────────────────────────────────────────────────────────────

class ActionHint(QWidget):
    clicked = Signal()

    def __init__(self, symbol: str, label: str, badge_color: str = BADGE_GREY,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hover = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 12, 0)
        layout.setSpacing(7)
        self._badge = QLabel(symbol)
        self._badge.setFixedSize(28, 28)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_badge(badge_color)
        self._text = QLabel(label)
        self._text.setStyleSheet(
            f"color:{TEXT_PRIMARY};font-size:13px;font-weight:500;")
        layout.addWidget(self._badge)
        layout.addWidget(self._text)
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_bg()

    def _apply_badge(self, c: str) -> None:
        self._badge.setStyleSheet(
            f"background:{c};color:#fff;border-radius:14px;"
            f"font-size:14px;font-weight:bold;")

    def _apply_bg(self) -> None:
        bg = "rgba(255,255,255,0.08)" if self._hover else "transparent"
        self.setStyleSheet(f"ActionHint{{background:{bg};border-radius:8px;}}")

    def set_badge_color(self, c: str) -> None: self._apply_badge(c)
    def set_label(self, t: str) -> None: self._text.setText(t)
    def set_symbol(self, s: str) -> None: self._badge.setText(s)
    def enterEvent(self, e) -> None: self._hover = True;  self._apply_bg()
    def leaveEvent(self, e) -> None: self._hover = False; self._apply_bg()
    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton: self.clicked.emit()


def _vdiv() -> QFrame:
    f = QFrame(); f.setObjectName("vdiv")
    f.setFrameShape(QFrame.Shape.VLine); f.setFixedHeight(22)
    return f

def _icon_label(symbol: str, size: int = 17) -> QLabel:
    lbl = QLabel(symbol)
    lbl.setStyleSheet(f"color:{TEXT_DIM};font-size:{size}px;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Castki")
        self.setStyleSheet(APP_STYLE)
        self.setMinimumSize(640, 420)

        self._formats: list = []
        self._audio = AudioPassthrough()
        self._recording = False
        self._vcam_active = False
        self._bar_open = False
        self._current_device: QCameraDevice | None = None
        self._settings = QSettings("Castki", "prefs")

        saved_path = self._settings.value("saves_dir", "")
        self._saves_dir = Path(saved_path) if saved_path else _DEFAULT_SAVES_DIR

        self._vcam = VirtualCamPublisher()
        self._setup_camera(get_shadowcast_device())
        self._build_ui()
        self._populate_formats()

        QTimer.singleShot(0, self._camera.start)

    # ── Camera ────────────────────────────────────────────────────────

    def _setup_camera(self, device: QCameraDevice | None) -> None:
        self._current_device = device
        self._camera = QCamera(device) if device else QCamera()
        self._session = QMediaCaptureSession()
        self._session.setCamera(self._camera)

        self._image_capture = QImageCapture()
        self._image_capture.imageSaved.connect(self._on_image_saved)
        self._session.setImageCapture(self._image_capture)

        sc_audio = next(
            (d for d in QMediaDevices.audioInputs()
             if "shadowcast" in d.description().lower()), None)
        self._audio_input = QAudioInput(sc_audio) if sc_audio else None
        if self._audio_input:
            self._session.setAudioInput(self._audio_input)

        self._recorder = QMediaRecorder()
        fmt = QMediaFormat()
        fmt.setFileFormat(QMediaFormat.FileFormat.MPEG4)
        fmt.setVideoCodec(QMediaFormat.VideoCodec.H264)
        fmt.setAudioCodec(QMediaFormat.AudioCodec.AAC)
        self._recorder.setMediaFormat(fmt)
        self._recorder.setQuality(QMediaRecorder.Quality.HighQuality)
        self._recorder.errorOccurred.connect(
            lambda err, msg: self._set_status(f"Error: {msg}", 5000))
        self._session.setRecorder(self._recorder)

        # Frame tap: use QVideoSink as primary output so we can intercept frames
        self._frame_sink = QVideoSink()
        self._frame_sink.videoFrameChanged.connect(self._on_video_frame)
        self._session.setVideoOutput(self._frame_sink)

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("videoRoot")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video area — clicking it toggles the control bar
        self._video_area = VideoArea()
        # QVideoWidget receives frames forwarded from _frame_sink
        self._video_area.clicked.connect(self._toggle_bar)
        layout.addWidget(self._video_area, stretch=1)

        # ── Control bar (hidden by default) ──────────────────────────
        self._bar = QWidget()
        self._bar.setObjectName("controlBar")
        self._bar.setFixedHeight(56)
        self._bar.setVisible(False)
        bl = QHBoxLayout(self._bar)
        bl.setContentsMargins(14, 0, 14, 0); bl.setSpacing(10)

        bl.addWidget(_icon_label("⊡", 17))
        self._format_combo = QComboBox()
        self._format_combo.currentIndexChanged.connect(self._on_format_changed)
        bl.addWidget(self._format_combo)
        bl.addSpacing(4); bl.addWidget(_vdiv()); bl.addSpacing(4)

        bl.addWidget(_icon_label("◗", 16))
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        saved_vol = int(self._settings.value("volume", 80))
        self._vol_slider.setValue(saved_vol)
        self._vol_slider.setFixedWidth(100)
        self._vol_slider.setEnabled(self._audio.available)
        self._vol_slider.valueChanged.connect(self._on_volume_changed)
        bl.addWidget(self._vol_slider)
        self._vol_pct = QLabel(f"{saved_vol}%")
        self._vol_pct.setObjectName("volPct")
        bl.addWidget(self._vol_pct)
        bl.addSpacing(4); bl.addWidget(_vdiv()); bl.addSpacing(4)

        self._hint_screenshot = ActionHint("◎", "Screenshot", BADGE_BLUE)
        self._hint_screenshot.clicked.connect(self._take_screenshot)
        bl.addWidget(self._hint_screenshot)

        self._hint_record = ActionHint("●", "Record", BADGE_GREY)
        self._hint_record.clicked.connect(self._toggle_record)
        bl.addWidget(self._hint_record)

        self._hint_fullscreen = ActionHint("⛶", "Fullscreen", BADGE_GREEN)
        self._hint_fullscreen.clicked.connect(self._toggle_fullscreen)
        bl.addWidget(self._hint_fullscreen)

        self._hint_vcam = ActionHint("⬡", "Virtual Cam", BADGE_GREY)
        self._hint_vcam.clicked.connect(self._toggle_vcam)
        bl.addWidget(self._hint_vcam)

        bl.addWidget(_vdiv())
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bl.addWidget(spacer)

        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        bl.addWidget(self._status_label)
        bl.addSpacing(6)

        self._device_btn = QPushButton("")
        self._device_btn.setObjectName("deviceBtn")
        self._device_btn.setMinimumWidth(160)
        self._device_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._device_btn.clicked.connect(self._show_device_menu)
        bl.addWidget(self._device_btn)

        self._gear_btn = QPushButton("⚙")
        self._gear_btn.setObjectName("gearBtn")
        self._gear_btn.setFixedSize(40, 40)
        self._gear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gear_btn.setToolTip("Settings")
        self._gear_btn.clicked.connect(self._open_settings)
        bl.addWidget(self._gear_btn)

        layout.addWidget(self._bar)

        self._status_timer = QTimer()
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self._status_label.setText(""))

    def _toggle_bar(self) -> None:
        self._bar_open = not self._bar_open
        self._bar.setVisible(self._bar_open)
        if not self.isFullScreen() and self._formats:
            idx = self._format_combo.currentIndex()
            if 0 <= idx < len(self._formats):
                res = self._formats[idx].resolution()
                self.resize(res.width(), res.height() + (56 if self._bar_open else 0))

    # ── Frame intercept ───────────────────────────────────────────────

    def _on_video_frame(self, frame: QVideoFrame) -> None:
        self._video_area.video_widget.videoSink().setVideoFrame(frame)
        if self._vcam_active:
            img = frame.toImage().convertToFormat(QImage.Format.Format_RGB888)
            arr = np.frombuffer(img.constBits(), dtype=np.uint8).reshape(
                img.height(), img.width(), 3).copy()
            self._vcam.send(arr)

    # ── Formats ───────────────────────────────────────────────────────

    def _populate_formats(self) -> None:
        device = self._camera.cameraDevice()
        self._format_combo.blockSignals(True)
        self._format_combo.clear()

        if device.isNull():
            self._device_btn.setText("No device  ▾")
            self._format_combo.blockSignals(False)
            return

        self._formats = list_formats(device)
        for fmt in self._formats:
            self._format_combo.addItem(format_label(fmt))

        saved_fmt = self._settings.value("format", "")
        idx = self._format_combo.findText(saved_fmt)
        self._format_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._format_combo.blockSignals(False)

        if self._formats:
            self._camera.setCameraFormat(
                self._formats[self._format_combo.currentIndex()])
            res = self._formats[self._format_combo.currentIndex()].resolution()
            self.resize(res.width(), res.height() + (56 if self._bar_open else 0))

        self._device_btn.setText(f"{device.description()}  ▾")

    # ── Device picker ─────────────────────────────────────────────────

    def _show_device_menu(self) -> None:
        menu = QMenu(self)
        current_id = self._current_device.id() if self._current_device else b""
        for dev in QMediaDevices.videoInputs():
            action = menu.addAction(dev.description())
            action.setCheckable(True)
            action.setChecked(dev.id() == current_id)
            action.triggered.connect(lambda checked, d=dev: self._switch_device(d))
        btn = self._device_btn
        pos = btn.mapToGlobal(btn.rect().topLeft())
        pos.setY(pos.y() - menu.sizeHint().height() - 4)
        menu.exec(pos)

    def _switch_device(self, device: QCameraDevice) -> None:
        if device.id() == (self._current_device.id() if self._current_device else b""):
            return
        self._stop_vcam()
        self._camera.stop()
        self._session.setCamera(None)
        self._camera = QCamera(device)
        self._current_device = device
        self._session.setCamera(self._camera)
        self._populate_formats()
        self._camera.start()

    # ── Settings ──────────────────────────────────────────────────────

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._saves_dir, self)
        if dlg.exec():
            self._saves_dir = dlg.saves_dir

    # ── Virtual camera ────────────────────────────────────────────────

    def _toggle_vcam(self) -> None:
        if not self._vcam_active:
            if not self._formats:
                self._set_status("No format selected", 3000)
                return
            fmt = self._formats[self._format_combo.currentIndex()]
            res = fmt.resolution()
            fps = int(fmt.maxFrameRate())
            err = self._vcam.start(res.width(), res.height(), fps)
            if err:
                self._set_status(err, 8000)
                return
            self._vcam_active = True
            self._hint_vcam.set_badge_color(BADGE_RED)
            self._hint_vcam.set_symbol("⏺")
            self._hint_vcam.set_label("Stop Cam")
            self._set_status("Virtual camera active", 3000)
        else:
            self._stop_vcam()

    def _stop_vcam(self) -> None:
        if not self._vcam_active:
            return
        self._vcam.stop()
        self._vcam_active = False
        self._hint_vcam.set_badge_color(BADGE_GREY)
        self._hint_vcam.set_symbol("⬡")
        self._hint_vcam.set_label("Virtual Cam")

    # ── Slots ─────────────────────────────────────────────────────────

    def _on_format_changed(self, index: int) -> None:
        if 0 <= index < len(self._formats):
            self._stop_vcam()
            self._camera.stop()
            fmt = self._formats[index]
            self._camera.setCameraFormat(fmt)
            self._camera.start()
            if not self.isFullScreen():
                res = fmt.resolution()
                self.resize(res.width(), res.height() + (56 if self._bar_open else 0))

    def _on_volume_changed(self, value: int) -> None:
        self._audio.set_volume(value / 100.0)
        self._vol_pct.setText(f"{value}%")

    def _take_screenshot(self) -> None:
        self._saves_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._image_capture.captureToFile(str(self._saves_dir / f"screenshot_{stamp}.jpg"))

    def _on_image_saved(self, _id: int, path: str) -> None:
        self._set_status("Screenshot saved", 3000)

    def _toggle_record(self) -> None:
        if not self._recording:
            self._saves_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self._recorder.setOutputLocation(
                QUrl.fromLocalFile(str(self._saves_dir / f"recording_{stamp}.mp4")))
            self._recorder.record()
            self._recording = True
            self._hint_record.set_badge_color(BADGE_RED)
            self._hint_record.set_symbol("■")
            self._hint_record.set_label("Stop")
        else:
            self._recorder.stop()
            self._recording = False
            self._hint_record.set_badge_color(BADGE_GREY)
            self._hint_record.set_symbol("●")
            self._hint_record.set_label("Record")
            self._set_status("Recording saved", 4000)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self._hint_fullscreen.set_symbol("⛶")
            self._hint_fullscreen.set_label("Fullscreen")
        else:
            self.showFullScreen()
            self._hint_fullscreen.set_symbol("✕")
            self._hint_fullscreen.set_label("Exit")

    def _set_status(self, msg: str, timeout: int = 0) -> None:
        self._status_label.setText(msg)
        self._status_timer.stop()
        if timeout:
            self._status_timer.start(timeout)

    # ── Input ─────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key == Qt.Key.Key_S:
            self._take_screenshot()
        elif key == Qt.Key.Key_R:
            self._toggle_record()
        elif key in (Qt.Key.Key_F, Qt.Key.Key_F11):
            self._toggle_fullscreen()
        elif key == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
            self._hint_fullscreen.set_symbol("⛶")
            self._hint_fullscreen.set_label("Fullscreen")
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        self._settings.setValue("volume", self._vol_slider.value())
        self._settings.setValue("format", self._format_combo.currentText())
        self._settings.setValue("saves_dir", str(self._saves_dir))
        self._stop_vcam()
        self._camera.stop()
        self._audio.stop()
        super().closeEvent(event)
