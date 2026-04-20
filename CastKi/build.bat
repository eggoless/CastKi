@echo off
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "Castki" ^
  --add-data "ui;ui" ^
  --add-data "utils;utils" ^
  main.py
echo Done. Output in dist\Castki.exe
