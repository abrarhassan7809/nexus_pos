from PySide6.QtWidgets import QApplication, QDialog
import sys
from pathlib import Path

# ── Make sure the project root is on sys.path so all packages resolve ──
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.schema import init_db
from utils.theme import STYLESHEET
from views.login import LoginDialog
from main_window import MainWindow


# ── Application state ─────────────────────────────────────────────
_app: QApplication | None = None
_win: MainWindow | None = None


def show_login() -> None:
    """Display the login dialog; on success open the main window."""
    global _win
    dlg = LoginDialog()
    if dlg.exec() == QDialog.DialogCode.Accepted:
        _win = MainWindow(dlg.user_data, on_logout=show_login)
        _win.show()
    else:
        if _app:
            _app.quit()


def main() -> None:
    global _app
    # ── Initialise database (creates file + seeds on first run) ───
    init_db()

    # ── Qt application ─────────────────────────────────────────────
    _app = QApplication(sys.argv)
    _app.setApplicationName("NEXUS POS")
    _app.setOrganizationName("Nexus")
    _app.setStyleSheet(STYLESHEET)

    show_login()
    sys.exit(_app.exec())


if __name__ == "__main__":
    main()
