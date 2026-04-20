import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def _resource(name: str) -> str:
    # Works both from source and from a PyInstaller --onefile bundle
    base = getattr(sys, "_MEIPASS", Path(__file__).parent)
    return str(Path(base) / name)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Castki")
    app.setOrganizationName("local")
    app.setWindowIcon(QIcon(_resource("CastKiLogo.png")))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
