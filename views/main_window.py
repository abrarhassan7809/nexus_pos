from __future__ import annotations
import sys
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QLabel,
    QMessageBox, QHBoxLayout, QFrame, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from utils.theme import ThemeManager
from datetime import datetime
from views.dashboard import DashboardTab
from views.pos import PosTab
from views.inventory import InventoryTab
from views.sales import SalesTab
from views.reports import ReportsTab
from views.expenses import ExpensesTab


class MainWindow(QMainWindow):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._is_admin = user['role'] == 'admin'
        self._tm = ThemeManager()
        self.setWindowTitle(f"Nexus POS  —  {user['full_name'] or user['username']}")

        screen = self.screen()
        if screen:
            geo = screen.availableGeometry()
            w = max(1100, int(geo.width()  * 0.82))
            h = max(680,  int(geo.height() * 0.85))
            self.resize(w, h)
            self.move(geo.x() + (geo.width() - w) // 2,
                      geo.y() + (geo.height() - h) // 2)
        else:
            self.resize(1280, 800)

        self.setMinimumSize(900, 600)
        self._build_ui()
        self._build_menu()
        self._setup_statusbar()

        # Connect theme change so topbar repaints
        self._tm.theme_changed.connect(self._on_theme_changed)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        from PySide6.QtWidgets import QVBoxLayout
        cv = QVBoxLayout(central)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)

        self._topbar = self._make_topbar()
        cv.addWidget(self._topbar)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cv.addWidget(self.tabs)

        self.setCentralWidget(central)
        self._add_tabs()

    def _make_topbar(self) -> QFrame:
        T = self._tm.palette
        topbar = QFrame()
        topbar.setFixedHeight(50)
        topbar.setStyleSheet(
            f"QFrame {{ background: {T['surface']}; "
            f"border-bottom: 1px solid {T['border']}; }}"
        )
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(8)

        brand = QLabel("NEXUS")
        brand.setStyleSheet(
            f"color: {T['accent']}; font-size: 17px; font-weight: 900; letter-spacing: 5px;")
        tb.addWidget(brand)

        pos_label = QLabel("POS")
        pos_label.setStyleSheet(
            f"color: {T['text_dim']}; font-size: 10px; letter-spacing: 3px; margin-left: 2px;")
        tb.addWidget(pos_label)
        tb.addStretch()

        badge_color = T['accent'] if self._is_admin else T['info']
        role_badge = QLabel(f" {self._user['role'].upper()} ")
        role_badge.setStyleSheet(
            f"background: {badge_color}22; color: {badge_color}; "
            f"border: 1px solid {badge_color}55; border-radius: 9px; "
            f"font-size: 10px; font-weight: 700; padding: 2px 5px;"
        )
        tb.addWidget(role_badge)

        user_lbl = QLabel(f"👤  {self._user['full_name'] or self._user['username']}")
        user_lbl.setStyleSheet(f"color: {T['text_muted']}; font-size: 12px; padding: 0 6px;")
        tb.addWidget(user_lbl)

        # ── Theme toggle button ────────────────────────────────────────────────
        self._theme_btn = QPushButton()
        self._theme_btn.setFixedSize(50, 40)
        self._theme_btn.setObjectName("ghost")
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.setToolTip("Toggle Light / Dark mode")
        self._update_theme_btn_icon()
        self._theme_btn.clicked.connect(self._toggle_theme)
        tb.addWidget(self._theme_btn)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("ghost")
        logout_btn.setFixedSize(80, 40)
        logout_btn.clicked.connect(self._logout)
        tb.addWidget(logout_btn)

        return topbar

    def _update_theme_btn_icon(self):
        icon = "☀️" if self._tm.is_dark() else "🌙"
        tip  = "Switch to Light mode" if self._tm.is_dark() else "Switch to Dark mode"
        self._theme_btn.setText(icon)
        self._theme_btn.setToolTip(tip)

    def _toggle_theme(self):
        self._tm.toggle()

    def _on_theme_changed(self, mode: str):
        """Re-apply all styles and refresh data views when theme changes."""
        self._update_theme_btn_icon()
        T = self._tm.palette

        # Re-style topbar frame
        self._topbar.setStyleSheet(
            f"QFrame {{ background: {T['surface']}; "
            f"border-bottom: 1px solid {T['border']}; }}"
        )

        # Force all ThemedTable instances to re-apply their stylesheet
        from widgets.base import ThemedTable
        for tbl in self.findChildren(ThemedTable):
            tbl._refresh_table_style()

        # Repaint all custom-painted widgets (charts etc.)
        self._repaint_children(self.tabs)

        # Refresh data in each tab so item foreground colours update
        for tab in [self.dashboard, self.inventory, self.sales, self.reports, self.expenses]:
            if hasattr(tab, 'refresh'):
                tab.refresh()

    def _repaint_children(self, widget: QWidget):
        widget.update()
        for child in widget.findChildren(QWidget):
            child.update()

    def _add_tabs(self):
        self.dashboard  = DashboardTab(self._user)
        self.pos        = PosTab(self._user)
        self.inventory  = InventoryTab(self._user)
        self.sales      = SalesTab(self._user)
        self.reports    = ReportsTab(self._user)
        self.expenses   = ExpensesTab(self._user)

        self.tabs.addTab(self.dashboard,  "📊  Dashboard")
        self.tabs.addTab(self.pos,        "🛒  Point of Sale")
        self.tabs.addTab(self.inventory,  "📦  Inventory")
        self.tabs.addTab(self.sales,      "🧾  Sales")
        self.tabs.addTab(self.reports,    "📈  Reports")
        self.tabs.addTab(self.expenses,   "💸  Expenses")

        if self._is_admin:
            from views.users import UsersTab
            self.users_tab = UsersTab(self._user)
            self.tabs.addTab(self.users_tab, "👥  Users")

        self.pos.order_completed.connect(self.dashboard.refresh)
        self.pos.order_completed.connect(self.sales.refresh)
        self.pos.order_completed.connect(self.inventory.refresh)
        # Reload POS product grid when inventory changes (add/edit/delete/stock adjust)
        self.inventory.products_changed.connect(self.pos._load_products)
        # Refresh dashboard when expenses/budget change
        self.expenses.budget_changed.connect(self.dashboard.refresh)

    # ── Menu ───────────────────────────────────────────────────────────────────
    def _build_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        new_order = QAction("New Order (POS)", self)
        new_order.setShortcut("Ctrl+N")
        new_order.triggered.connect(lambda: self.tabs.setCurrentWidget(self.pos))
        file_menu.addAction(new_order)
        file_menu.addSeparator()
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self._logout)
        file_menu.addAction(logout_action)
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        for i, name in enumerate(["Dashboard", "Point of Sale", "Inventory", "Sales", "Reports"]):
            act = QAction(name, self)
            act.triggered.connect(lambda _, idx=i: self.tabs.setCurrentIndex(idx))
            view_menu.addAction(act)
        view_menu.addSeparator()
        theme_action = QAction("Toggle Light / Dark Mode", self)
        theme_action.setShortcut("Ctrl+Shift+T")
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)

        help_menu = menubar.addMenu("Help")
        about = QAction("About Nexus POS", self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    # ── Status bar ─────────────────────────────────────────────────────────────
    def _setup_statusbar(self):
        sb = self.statusBar()
        self._status_user  = QLabel(
            f"  Logged in: {self._user['username']}  ({self._user['role']})")
        self._status_clock = QLabel()
        sb.addWidget(self._status_user)
        sb.addPermanentWidget(self._status_clock)
        self._update_clock()

    def _update_clock(self):
        self._status_clock.setText(
            datetime.now().strftime("  %A, %d %B %Y  |  %H:%M:%S  "))

    # ── Actions ────────────────────────────────────────────────────────────────
    def _logout(self):
        if QMessageBox.question(
                self, "Logout", "Are you sure you want to logout?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.close()
            import subprocess
            subprocess.Popen([sys.executable, "main.py"])

    def _show_about(self):
        QMessageBox.about(
            self, "About Nexus POS",
            "<b>Nexus POS v1.0</b><br>"
            "A full-featured Point of Sale system<br>"
            "Built with PySide6 and SQLite<br><br>"
            "Features: Inventory, Billing, Reports, PDF Export<br>"
            "Theme: Light / Dark toggle (Ctrl+Shift+T)"
        )