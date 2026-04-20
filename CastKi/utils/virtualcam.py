from __future__ import annotations

import numpy as np

try:
    import pyvirtualcam
    _PVC_AVAILABLE = True
except ImportError:
    _PVC_AVAILABLE = False


class VirtualCamPublisher:
    def __init__(self) -> None:
        self._cam = None

    @property
    def available(self) -> bool:
        return _PVC_AVAILABLE

    def start(self, width: int, height: int, fps: int) -> str | None:
        """Return None on success, or an error string describing the failure."""
        if not _PVC_AVAILABLE:
            return "pyvirtualcam not installed — run: pip install pyvirtualcam"
        try:
            self._cam = pyvirtualcam.Camera(
                width=width, height=height, fps=fps,
                fmt=pyvirtualcam.PixelFormat.RGB,
                backend="obs",
            )
            print(f"[vcam] started {width}x{height} @ {fps}fps → {self._cam.device}")
            return None
        except Exception as e:
            print(f"[vcam] failed to start: {e}")
            self._cam = None
            return str(e)

    @property
    def running(self) -> bool:
        return self._cam is not None

    def send(self, frame_rgb: np.ndarray) -> None:
        if self._cam is not None:
            try:
                self._cam.send(frame_rgb)
            except Exception:
                pass

    def stop(self) -> None:
        if self._cam is not None:
            try:
                self._cam.close()
            except Exception:
                pass
            self._cam = None
            print("[vcam] stopped")
