import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from database import init_db
from utils.theme import ThemeManager
from views.login import LoginDialog
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nexus POS")
    app.setOrganizationName("NexusSoft")
    app.setStyle("Fusion")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Apply initial theme (dark by default)
    tm = ThemeManager()
    tm.apply()

    init_db()

    while True:
        login = LoginDialog()
        if login.exec() != LoginDialog.DialogCode.Accepted:
            break
        user = login.get_user()
        if user is None:
            break
        window = MainWindow(user)
        window.show()
        app.exec()
        break

    sys.exit(0)


if __name__ == "__main__":
    main()
