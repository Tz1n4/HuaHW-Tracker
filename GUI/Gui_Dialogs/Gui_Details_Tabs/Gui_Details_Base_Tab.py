#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Details_Base_Tab.py — базовый каркас для вкладок детального анализа.
Содержит таблицу, стили, логику подсветки критических значений.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QAbstractItemView, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class BaseDetailsTab(QWidget):
    """Базовый класс вкладки. Наследники должны реализовать метод _populate_table."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e; color: #d4d4d4;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d; color: #d4d4d4;
                border: 1px solid #3c3c3c; padding: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

    def setup_columns(self, headers):
        """Устанавливает заголовки таблицы."""
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

    def apply_row_color(self, row, days_left):
        """Подсвечивает строку в зависимости от остатка дней (если применимо)."""
        if not isinstance(days_left, int):
            return

        color = None
        if days_left < 0:
            color = QColor(255, 80, 80)
        elif days_left < 180:
            color = QColor(255, 180, 50)

        if color:
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setForeground(color)

    def finalize_table(self):
        """Вызывается после заполнения данными."""
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)