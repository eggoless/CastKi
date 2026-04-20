# Castki — Local Replacement for Genki Arcade

## Problem
Genki Arcade (arcade.genkithings.com) requires a full browser, requests unnecessary microphone access,
and runs in the cloud. We want a 100% local, native desktop app with the same feature set.

## Stack
- **Python 3.12**
- **PySide6** — Qt 6 native GUI, hardware-accelerated video via DirectX
- **pycaw** — Windows audio volume control
- **PyInstaller** — package to single `.exe`

## Features (parity with Genki Arcade)
| Feature | Qt 6 API |
|---|---|
| Live video feed (no mic) | `QCamera` → `QMediaCaptureSession` → `QVideoWidget` |
| Resolution & FPS selector | `QCameraDevice.videoFormats()` |
| Volume slider | `pycaw` Windows audio mixer |
| Screenshot | `QImageCapture` |
| Record | `QMediaRecorder` |
| Fullscreen toggle | `QMainWindow.showFullScreen()` |

## File Layout
```
genki/
  PLAN.md               ← this file
  main.py               ← app entry point
  ui/
    main_window.py      ← QMainWindow, toolbar, controls
    video_widget.py     ← camera session setup
  utils/
    audio.py            ← pycaw volume helpers
    devices.py          ← enumerate cameras + formats
  requirements.txt
  build.bat             ← PyInstaller one-liner
```

## Build Phases
1. **Scaffold** — project structure, requirements.txt, venv
2. **Device enumeration** — list cameras, list supported formats
3. **Live viewer** — camera feed in a window, no controls yet
4. **Controls** — resolution/FPS dropdowns, volume slider, toolbar buttons
5. **Screenshot** — capture still to timestamped file
6. **Recording** — start/stop, save to file
7. **Fullscreen** — toggle with F or button
8. **Packaging** — PyInstaller single exe

## Non-goals
- No microphone access
- No network calls of any kind
- No auto-update / telemetry
