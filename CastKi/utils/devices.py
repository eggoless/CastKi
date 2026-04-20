from PySide6.QtMultimedia import QMediaDevices, QCameraDevice, QCameraFormat
from PySide6.QtCore import QSize


def get_shadowcast_device() -> QCameraDevice | None:
    devices = QMediaDevices.videoInputs()
    for dev in devices:
        desc = dev.description().lower()
        if any(k in desc for k in ("shadowcast", "genki", "capture", "hdmi")):
            return dev
    return QMediaDevices.defaultVideoInput() if devices else None


def list_formats(device: QCameraDevice) -> list[QCameraFormat]:
    """Return unique formats, no 25fps, sorted by resolution then frame rate descending."""
    seen: set[tuple[int, int, int]] = set()
    result: list[QCameraFormat] = []

    all_formats = sorted(
        device.videoFormats(),
        key=lambda f: (f.resolution().width() * f.resolution().height(), f.maxFrameRate()),
        reverse=True,
    )

    for fmt in all_formats:
        fps = int(fmt.maxFrameRate())
        if fps == 25:
            continue
        key = (fmt.resolution().width(), fmt.resolution().height(), fps)
        if key in seen:
            continue
        seen.add(key)
        result.append(fmt)

    return result


def format_label(fmt: QCameraFormat) -> str:
    res: QSize = fmt.resolution()
    fps = int(fmt.maxFrameRate())
    return f"{res.width()}x{res.height()} @ {fps}fps"
