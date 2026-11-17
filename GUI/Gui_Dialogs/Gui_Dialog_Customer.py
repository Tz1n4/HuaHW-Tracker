#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Dialog_Customer.py — диалог ввода Заказчика / Проекта.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout
from PyQt6.QtGui import QFont

from Utils.Utils_Locale import tr


class CustomerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("cust_dialog_title"))
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel(tr("cust_dialog_header"))
        header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(header)

        hint = QLabel(tr("cust_dialog_hint"))
        hint.setStyleSheet("color: #888;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)

        self.customer_edit = QLineEdit()
        form.addRow(tr("cust_label_customer"), self.customer_edit)

        self.project_edit = QLineEdit()
        form.addRow(tr("cust_label_project"), self.project_edit)

        layout.addLayout(form)
        layout.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton(tr("cust_continue"))
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

        self.customer_edit.setFocus()

    def values(self):
        return (
            self.customer_edit.text().strip(),
            self.project_edit.text().strip(),
        )