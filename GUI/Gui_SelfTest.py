#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_SelfTest.py — диалоговое окно Self-test.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from Utils.Utils_Locale import tr, trf
from Utils.Utils_SelfTest import run_checks


class SelfTestDialog(QDialog):
    def __init__(self, parent=None, test_file=None):
        super().__init__(parent)
        self.setWindowTitle(tr("selftest_title"))
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        try:
            results = run_checks(test_file=test_file)
        except Exception as e:
            results = [{"group": "Error", "subgroup": "", "label": str(e), "ok": False, "extra": ""}]

        ok_count = sum(1 for r in results if r["ok"])
        fail_count = len(results) - ok_count

        summary = QLabel(trf("selftest_result", ok=ok_count, fail=fail_count))
        summary.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(summary)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Параметр", "Статус", "Значение / Адрес"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 250)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 4px;
            }
        """)

        last_group = None
        last_subgroup = None
        
        for r in results:
            # Заголовок группы
            if r["group"] != last_group:
                last_group = r["group"]
                last_subgroup = None
                row = self.table.rowCount()
                self.table.insertRow(row)
                item = QTableWidgetItem(last_group)
                font = QFont("Arial", 11, QFont.Weight.Bold)
                item.setFont(font)
                item.setBackground(QColor("#1e1e1e"))
                item.setForeground(QColor("#569CD6"))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item)
                self.table.setSpan(row, 0, 1, 3)
            
            # Заголовок подгруппы
            if r["subgroup"] and r["subgroup"] != last_subgroup:
                last_subgroup = r["subgroup"]
                row = self.table.rowCount()
                self.table.insertRow(row)
                item = QTableWidgetItem(last_subgroup)
                font = QFont("Arial", 10, QFont.Weight.Bold)
                item.setFont(font)
                item.setBackground(QColor("#1e1e1e"))
                item.setForeground(QColor("#569CD6"))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item)
                self.table.setSpan(row, 0, 1, 3)
            
            # Строка с данными
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            label_item = QTableWidgetItem(r["label"])
            label_item.setForeground(QColor("#cccccc"))
            
            mark_item = QTableWidgetItem("✓" if r["ok"] else "✗")
            mark_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = QColor("#4CAF50") if r["ok"] else QColor("#F44336")
            mark_item.setForeground(color)
            mark_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            
            extra_text = r.get("extra", "")
            
            if r.get("group") == "HW-Tracker Files" and "Script folder" not in r["label"]:
                sub = r.get("subgroup", "")
                if sub == "Core":
                    extra_text = f"Core/{r['label']}.py"
                elif sub == "GUI":
                    extra_text = f"GUI/{r['label']}.py"
                elif sub == "GUI_Dialogs":
                    extra_text = f"GUI/Gui_Dialogs/{r['label']}.py"
                elif sub == "GUI_Details_Tabs":
                    extra_text = f"GUI/Gui_Dialogs/Gui_Details_Tabs/{r['label']}.py"
                elif sub == "Parsers":
                    extra_text = f"Parsers/{r['label']}.py"
                elif sub == "Parsers_Details":
                    extra_text = f"Parsers/Parsers_Details/{r['label']}.py"
                elif sub == "Utils":
                    extra_text = f"Utils/{r['label']}.py"
            
            extra_item = QTableWidgetItem(extra_text)
            extra_item.setForeground(QColor("#888888"))
            
            self.table.setItem(row, 0, label_item)
            self.table.setItem(row, 1, mark_item)
            self.table.setItem(row, 2, extra_item)

        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()

        copy_btn = QPushButton(tr("selftest_copy"))
        copy_btn.clicked.connect(self._copy_to_clipboard)

        close_btn = QPushButton(tr("close"))
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(copy_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self.status_text = trf("selftest_status", ok=ok_count, fail=fail_count)

    def _copy_to_clipboard(self):
        text_lines = []
        for row in range(self.table.rowCount()):
            cols = []
            for col in range(3):
                item = self.table.item(row, col)
                cols.append(item.text() if item else "")
            if cols[1]:
                text_lines.append(f"[{cols[1]}] {cols[0]} — {cols[2]}")
            else:
                text_lines.append(cols[0])
        QApplication.clipboard().setText("\n".join(text_lines))