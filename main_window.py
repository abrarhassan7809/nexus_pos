from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QLabel, QPushButton, QTabWidget, QMessageBox)
from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from utils.theme import THEME
from views.dashboard import DashboardTab
from views.pos import PosTab
from views.inventory import InventoryTab
from views.sales import SalesTab
from views.reports import ReportsTab
from views.users import UsersTab


class MainWindow(QMainWindow):
    """
    Top-level window.  Receives the authenticated *user* dict and builds
    the tab layout accordingly (admin gets the Users tab, cashiers don't).
    """

    def __init__(self, user: dict, on_logout=None):
        super().__init__()
        self.current_user = user
        self._on_logout_cb = on_logout          # callable to show login again
        title = (
            f"NEXUS POS  —  "
            f"{user.get('full_name') or user['username']}  "
            f"[{user['role'].upper()}]"
        )
        self.setWindowTitle(title)
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)
        self._build_ui()
        self._start_clock()

    # ── UI ────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        QHBoxLayout(central).setContentsMargins(0, 0, 0, 0)

        # ── Tabs (West = left-side vertical tabs) ─────────────────
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: transparent;
                color: #8892AA;
                border: none;
                border-left: 3px solid transparent;
                padding: 14px 10px 14px 20px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                min-width: 160px;
            }
            QTabBar::tab:selected {
                background: #1C2130;
                color: #FF6B35;
                border-left: 3px solid #FF6B35;
            }
            QTabBar::tab:hover:!selected {
                background: #1A2030;
                color: #EAEDF5;
            }
        """)

        # ── Instantiate tab views ──────────────────────────────────
        self.dash_tab  = DashboardTab()
        self.pos_tab   = PosTab(self.current_user)
        self.inv_tab   = InventoryTab(self.current_user)
        self.sales_tab = SalesTab()
        self.rep_tab   = ReportsTab()

        self.tabs.addTab(self.dash_tab,  "🏠  Dashboard")
        self.tabs.addTab(self.pos_tab,   "🛒  New Order")
        self.tabs.addTab(self.inv_tab,   "📦  Inventory")
        self.tabs.addTab(self.sales_tab, "🧾  Sales")
        self.tabs.addTab(self.rep_tab,   "📊  Reports")

        if self.current_user["role"] == "admin":
            self.users_tab = UsersTab()
            self.tabs.addTab(self.users_tab, "👤  Users")

        # Wire cross-tab signals
        self.pos_tab.order_saved.connect(self.dash_tab.refresh)
        self.pos_tab.order_saved.connect(self.inv_tab.refresh)
        self.tabs.currentChanged.connect(self._on_tab_change)

        central.layout().addWidget(self.tabs)

        # ── Status bar ─────────────────────────────────────────────
        sb = self.statusBar()

        self._user_lbl = QLabel(
            f"  👤  {self.current_user.get('full_name') or self.current_user['username']}"
            f"  [{self.current_user['role'].upper()}]  "
        )
        self._user_lbl.setStyleSheet(f"color: {THEME['accent']}; font-weight: 700;")

        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet(f"color: {THEME['text_secondary']};")

        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setFixedHeight(24)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {THEME['danger']};
                border: 1px solid {THEME['danger']};
                border-radius: 4px;
                padding: 2px 10px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: {THEME['danger']}; color: white; }}
        """)
        logout_btn.clicked.connect(self._logout)

        sb.addPermanentWidget(self._user_lbl)
        sb.addPermanentWidget(self._clock_lbl)
        sb.addPermanentWidget(logout_btn)

    # ── Slots ─────────────────────────────────────────────────────
    def _on_tab_change(self, index: int) -> None:
        tab = self.tabs.widget(index)
        if hasattr(tab, "refresh"):
            tab.refresh()

    def _start_clock(self) -> None:
        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self) -> None:
        self._clock_lbl.setText(
            "  🕐  " + datetime.now().strftime("%H:%M:%S  %Y-%m-%d")
        )

    def _logout(self) -> None:
        answer = QMessageBox.question(
            self, "Logout", "Log out of NEXUS POS?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.close()
            if callable(self._on_logout_cb):
                self._on_logout_cb()
