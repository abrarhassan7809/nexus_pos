#!/usr/bin/env python3
"""
Nexus POS — Point of Sale System
Entry point: initializes DB, shows login, launches main window.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt

from database import init_db
from utils.theme import STYLESHEET
from views.login import LoginDialog
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nexus POS")
    app.setOrganizationName("NexusSoft")
    app.setStyle("Fusion")

    # Apply global stylesheet
    app.setStyleSheet(STYLESHEET)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Initialize database (creates tables + seed data)
    init_db()

    # Show login dialog
    while True:
        login = LoginDialog()
        if login.exec() != LoginDialog.DialogCode.Accepted:
            # User closed login — exit app
            break

        user = login.get_user()
        if user is None:
            break

        # Launch main window
        window = MainWindow(user)
        window.show()
        app.exec()

        # After main window closes, loop back to login
        # (allows switching accounts without restarting)
        break  # Remove this break to enable re-login after logout

    sys.exit(0)


if __name__ == "__main__":
    main()
