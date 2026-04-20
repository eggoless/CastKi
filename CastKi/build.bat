@echo off
echo Building CastKi...
cd /d "%~dp0"

if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

pyinstaller ^
  --onefile ^
  --windowed ^
  --name "CastKi" ^
  --collect-all PySide6 ^
  --hidden-import sounddevice ^
  --collect-binaries sounddevice ^
  --hidden-import pyvirtualcam ^
  --collect-binaries pyvirtualcam ^
  main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful^^!  Output: dist\CastKi.exe
) else (
    echo.
    echo Build FAILED. See output above.
)
pause
