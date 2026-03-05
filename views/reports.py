from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QDateEdit, QScrollArea, QHeaderView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from database import ReportQueries
from utils import format_currency, today_str
from utils.theme import THEME as T
from widgets import (SectionTitle, StatCard, Divider,
                     WeeklyBarChart, TopProductsChart,
                     styled_table, make_table_item)

RIGHT  = Qt.AlignmentFlag.AlignRight  | Qt.AlignmentFlag.AlignVCenter
CENTER = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter


class ReportsTab(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self._user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Reports & Analytics"))
        hdr.addStretch()
        refresh_btn = QPushButton("⟳  Refresh")
        refresh_btn.setObjectName("ghost")
        refresh_btn.setFixedHeight(34)
        refresh_btn.clicked.connect(self.refresh)
        hdr.addWidget(refresh_btn)
        pdf_btn = QPushButton("📄  Export Report PDF")
        pdf_btn.setObjectName("primary")
        pdf_btn.setFixedHeight(34)
        pdf_btn.clicked.connect(self._export_pdf)
        hdr.addWidget(pdf_btn)
        layout.addLayout(hdr)

        # Sub-tabs
        tabs = QTabWidget()

        # ── Overview ───────────────────────────────────────────────────────────
        ov_scroll = QScrollArea()
        ov_scroll.setWidgetResizable(True)
        ov_scroll.setFrameShape(QFrame.Shape.NoFrame)
        ov_cont = QWidget()
        ov = QVBoxLayout(ov_cont)
        ov.setContentsMargins(12, 12, 12, 12)
        ov.setSpacing(14)

        dr_row = QHBoxLayout()
        dr_row.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 7 days", "Last 14 days", "Last 30 days", "This Month"])
        self.period_combo.setFixedHeight(32)
        self.period_combo.currentIndexChanged.connect(self.refresh)
        dr_row.addWidget(self.period_combo)
        dr_row.addStretch()
        ov.addLayout(dr_row)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self.card_revenue = StatCard("Total Revenue",    "—", T['success'], "💰")
        self.card_orders  = StatCard("Total Orders",     "—", T['accent'],  "🧾")
        self.card_avg     = StatCard("Avg Order Value",  "—", T['info'],    "📊")
        self.card_items   = StatCard("Items Sold",       "—", T['warning'], "📦")
        for c in [self.card_revenue, self.card_orders, self.card_avg, self.card_items]:
            cards_row.addWidget(c)
        ov.addLayout(cards_row)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        sales_card = QFrame(); sales_card.setObjectName("card")
        sc = QVBoxLayout(sales_card); sc.setContentsMargins(14, 14, 14, 14); sc.setSpacing(8)
        lbl = QLabel("📊  Daily Revenue"); lbl.setStyleSheet("font-weight:600;")
        sc.addWidget(lbl); sc.addWidget(Divider())
        self.sales_chart = WeeklyBarChart()
        self.sales_chart.setMinimumHeight(220)
        sc.addWidget(self.sales_chart)
        charts_row.addWidget(sales_card, 3)

        top_card = QFrame(); top_card.setObjectName("card")
        tc = QVBoxLayout(top_card); tc.setContentsMargins(14, 14, 14, 14); tc.setSpacing(8)
        lbl2 = QLabel("🏆  Top Products"); lbl2.setStyleSheet("font-weight:600;")
        tc.addWidget(lbl2); tc.addWidget(Divider())
        self.top_chart = TopProductsChart()
        self.top_chart.setMinimumHeight(220)
        tc.addWidget(self.top_chart)
        charts_row.addWidget(top_card, 2)
        ov.addLayout(charts_row)

        ov_scroll.setWidget(ov_cont)
        tabs.addTab(ov_scroll, "📈  Overview")

        # ── Monthly ────────────────────────────────────────────────────────────
        monthly_w = QWidget()
        ml = QVBoxLayout(monthly_w)
        ml.setContentsMargins(12, 12, 12, 12); ml.setSpacing(10)
        ml.addWidget(QLabel("Monthly Sales Summary"))
        # Month=120, Transactions=110, Revenue=110, Discounts=110, Net=stretch
        self.monthly_table = styled_table(
            ["Month", "Transactions", "Revenue", "Discounts", "Net Revenue"],
            col_widths=[120, 110, 110, 110, None], stretch_col=4
        )
        ml.addWidget(self.monthly_table)
        tabs.addTab(monthly_w, "📅  Monthly")

        # ── Daily Detail ───────────────────────────────────────────────────────
        daily_w = QWidget()
        dl = QVBoxLayout(daily_w)
        dl.setContentsMargins(12, 12, 12, 12); dl.setSpacing(10)
        dr2 = QHBoxLayout()
        dr2.addWidget(QLabel("Select Month:"))
        self.month_combo = QComboBox()
        self.month_combo.setFixedHeight(32)
        now = QDate.currentDate()
        for i in range(12):
            d = now.addMonths(-i)
            self.month_combo.addItem(d.toString("MMMM yyyy"), (d.year(), d.month()))
        self.month_combo.currentIndexChanged.connect(self._load_daily)
        dr2.addWidget(self.month_combo)
        dr2.addStretch()
        dl.addLayout(dr2)
        # Date=120, Transactions=110, Revenue=stretch
        self.daily_table = styled_table(
            ["Date", "Transactions", "Revenue"],
            col_widths=[130, 120, None], stretch_col=2
        )
        dl.addWidget(self.daily_table)
        tabs.addTab(daily_w, "📆  Daily Detail")

        # ── Top Products ───────────────────────────────────────────────────────
        top_w = QWidget()
        tl = QVBoxLayout(top_w)
        tl.setContentsMargins(12, 12, 12, 12); tl.setSpacing(10)
        tf = QHBoxLayout()
        tf.addWidget(QLabel("From:"))
        self.top_from = QDateEdit()
        self.top_from.setCalendarPopup(True)
        self.top_from.setDate(QDate.currentDate().addDays(-30))
        self.top_from.setFixedHeight(32)
        tf.addWidget(self.top_from)
        tf.addWidget(QLabel("To:"))
        self.top_to = QDateEdit()
        self.top_to.setCalendarPopup(True)
        self.top_to.setDate(QDate.currentDate())
        self.top_to.setFixedHeight(32)
        tf.addWidget(self.top_to)
        go_btn = QPushButton("Apply")
        go_btn.setObjectName("primary")
        go_btn.setFixedHeight(32)
        go_btn.clicked.connect(self._load_top_products)
        tf.addWidget(go_btn)
        tf.addStretch()
        tl.addLayout(tf)
        # Rank=50, Product=stretch, Qty=100, Revenue=110
        self.top_table = styled_table(
            ["#", "Product", "Qty Sold", "Revenue"],
            col_widths=[50, None, 100, 110], stretch_col=1
        )
        tl.addWidget(self.top_table)
        tabs.addTab(top_w, "🏆  Top Products")

        layout.addWidget(tabs)

    def refresh(self):
        from datetime import datetime, timedelta
        period = self.period_combo.currentText()
        days = {"Last 7 days": 7, "Last 14 days": 14,
                "Last 30 days": 30, "This Month": QDate.currentDate().day()}.get(period, 7)
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to   = today_str()

        rows = ReportQueries.weekly_sales(max(1, days // 7 + 1))
        self.sales_chart.set_data([(r['day'], r['revenue']) for r in rows])

        total_rev = sum(r['revenue'] for r in rows)
        total_tx  = sum(r['tx_count'] for r in rows)
        avg = total_rev / total_tx if total_tx else 0
        self.card_revenue.set_value(format_currency(total_rev))
        self.card_orders.set_value(str(total_tx))
        self.card_avg.set_value(format_currency(avg))

        top = ReportQueries.top_products(8, date_from, date_to)
        self.top_chart.set_data([(r['name'], r['revenue'] or 0) for r in top])

        from database.connection import get_db
        conn = get_db()
        try:
            row = conn.execute(
                """SELECT COALESCE(SUM(oi.qty),0) as total_qty
                   FROM order_items oi JOIN orders o ON oi.order_id=o.id
                   WHERE o.status='completed' AND date(o.created_at)>=?""",
                (date_from,)
            ).fetchone()
            self.card_items.set_value(str(int(row['total_qty'])))
        finally:
            conn.close()

        # Monthly summary
        monthly = ReportQueries.monthly_summary_list()
        self.monthly_table.setRowCount(0)
        self.monthly_table.setRowCount(len(monthly))
        for i, r in enumerate(monthly):
            self.monthly_table.setItem(i, 0, QTableWidgetItem(r['month']))
            self.monthly_table.setItem(i, 1, make_table_item(str(r['tx_count']), CENTER))
            self.monthly_table.setItem(i, 2, make_table_item(
                format_currency(r['revenue'] or 0), RIGHT, T['success']))
            self.monthly_table.setItem(i, 3, make_table_item(
                format_currency(r['discounts'] or 0), RIGHT, T['warning']))
            net = (r['revenue'] or 0) - (r['discounts'] or 0)
            self.monthly_table.setItem(i, 4, make_table_item(format_currency(net), RIGHT))

        self._load_daily()
        self._load_top_products()

    def _load_daily(self):
        data = self.month_combo.currentData()
        if not data:
            return
        year, month = data
        rows = ReportQueries.monthly_sales(year, month)
        self.daily_table.setRowCount(0)
        self.daily_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.daily_table.setItem(i, 0, QTableWidgetItem(r['day']))
            self.daily_table.setItem(i, 1, make_table_item(str(r['tx_count']), CENTER))
            self.daily_table.setItem(i, 2, make_table_item(
                format_currency(r['revenue'] or 0), RIGHT, T['success']))

    def _load_top_products(self):
        date_from = self.top_from.date().toString("yyyy-MM-dd")
        date_to   = self.top_to.date().toString("yyyy-MM-dd")
        rows = ReportQueries.top_products(20, date_from, date_to)
        self.top_table.setRowCount(0)
        self.top_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.top_table.setItem(i, 0, make_table_item(str(i + 1), CENTER))
            self.top_table.setItem(i, 1, QTableWidgetItem(r['name']))
            self.top_table.setItem(i, 2, make_table_item(str(r['total_qty']), CENTER))
            self.top_table.setItem(i, 3, make_table_item(
                format_currency(r['revenue'] or 0), RIGHT, T['success']))

    def _export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                             Spacer, Table, TableStyle)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from datetime import datetime

            path, _ = QFileDialog.getSaveFileName(
                self, "Save Report", f"nexus_report_{today_str()}.pdf", "PDF Files (*.pdf)")
            if not path:
                return

            doc = SimpleDocTemplate(path, pagesize=A4,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm,
                                    leftMargin=2*cm, rightMargin=2*cm)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('t', parent=styles['Title'],
                                          fontSize=20, spaceAfter=6,
                                          textColor=colors.HexColor('#6C63FF'))
            story = [
                Paragraph("NEXUS POS — Sales Report", title_style),
                Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                          styles['Normal']),
                Spacer(1, 0.5*cm),
            ]

            # Monthly table
            story.append(Paragraph("Monthly Sales Summary", styles['Heading2']))
            monthly = ReportQueries.monthly_summary_list()
            tdata = [["Month", "Transactions", "Revenue", "Discounts"]]
            for r in monthly[:12]:
                tdata.append([r['month'], str(r['tx_count']),
                               f"${r['revenue']:,.2f}" if r['revenue'] else "$0.00",
                               f"${r['discounts']:,.2f}" if r['discounts'] else "$0.00"])
            t = Table(tdata, colWidths=[4*cm, 3*cm, 4*cm, 4*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), colors.HexColor('#6C63FF')),
                ('TEXTCOLOR',  (0,0),(-1,0), colors.white),
                ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0,0),(-1,-1), 10),
                ('GRID',       (0,0),(-1,-1), 0.5, colors.HexColor('#2E3248')),
                ('ROWBACKGROUNDS', (0,1),(-1,-1),
                 [colors.HexColor('#1A1D27'), colors.HexColor('#222535')]),
                ('TEXTCOLOR',  (0,1),(-1,-1), colors.HexColor('#E8EAF0')),
                ('ALIGN',      (1,1),(-1,-1), 'RIGHT'),
                ('PADDING',    (0,0),(-1,-1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*cm))

            # Top products
            story.append(Paragraph("Top 10 Products (All Time)", styles['Heading2']))
            top = ReportQueries.top_products(10)
            tdata2 = [["#", "Product", "Qty Sold", "Revenue"]]
            for i, r in enumerate(top, 1):
                tdata2.append([str(i), r['name'], str(r['total_qty']),
                                f"${r['revenue']:,.2f}" if r['revenue'] else "$0.00"])
            t2 = Table(tdata2, colWidths=[1*cm, 8*cm, 3*cm, 4*cm])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), colors.HexColor('#22C55E')),
                ('TEXTCOLOR',  (0,0),(-1,0), colors.white),
                ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0,0),(-1,-1), 10),
                ('GRID',       (0,0),(-1,-1), 0.5, colors.HexColor('#2E3248')),
                ('ROWBACKGROUNDS', (0,1),(-1,-1),
                 [colors.HexColor('#1A1D27'), colors.HexColor('#222535')]),
                ('TEXTCOLOR',  (0,1),(-1,-1), colors.HexColor('#E8EAF0')),
                ('ALIGN',      (2,1),(-1,-1), 'RIGHT'),
                ('PADDING',    (0,0),(-1,-1), 6),
            ]))
            story.append(t2)

            doc.build(story)
            QMessageBox.information(self, "Exported", f"Report saved to:\n{path}")

        except ImportError:
            QMessageBox.warning(self, "Missing Library",
                                "Install reportlab:\npip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
