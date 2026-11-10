#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Details_BBU_Tab.py — вкладка детального анализа BBU.
"""

import os
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt

from GUI.Gui_Dialogs.Gui_Details_Tabs.Gui_Details_Base_Tab import BaseDetailsTab
from Parsers.Parsers_Details.Parser_BBU_Details import parse_bbu_details
from Core.Core_System_Info import parse_system_info


class BBUDetailsTab(BaseDetailsTab):
    """Вкладка с детальной информацией по BBU."""

    def __init__(self, file_paths, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self._last_bbu_data = []
        
        headers = [
            "Система", "Модель СХД", "Серийный номер СХД", "ID (Слот)", 
            "Здоровье", "Статус", "Напряжение", 
            "Остаток (дн. из лога)", "Остаток на сегодня (дн.)", "Конец срока", 
            "Поставка", "Возраст", "Part Number", "Серийный номер"
        ]
        self.setup_columns(headers)
        
        self._load_data()

    def _load_data(self):
        all_bbu_data = []
        
        for fpath in self.file_paths:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                sys_info = parse_system_info(content[:5000])
                sys_name = sys_info.get("name", os.path.basename(fpath))
                sys_model = sys_info.get("model", "N/A")
                sys_version = sys_info.get("version", "V3")
                sys_serial = sys_info.get("serial", "N/A")
                
                bbu_list = parse_bbu_details(content, sys_version=sys_version)
                
                for bbu in bbu_list:
                    bbu["sys_name"] = sys_name
                    bbu["sys_model"] = sys_model
                    bbu["sys_serial"] = sys_serial
                    all_bbu_data.append(bbu)
            except Exception as e:
                print(f"Ошибка при чтении {fpath}: {e}")

        self._last_bbu_data = all_bbu_data
        self._populate_table()

    def _populate_table(self):
        if not self._last_bbu_data:
            return

        self.table.setRowCount(len(self._last_bbu_data))
        
        for row, bbu in enumerate(self._last_bbu_data):
            age_str = "N/A"
            if isinstance(bbu.get("age_days"), int):
                age_years = bbu["age_days"] // 365
                age_rem_days = bbu["age_days"] % 365
                if age_years > 0:
                    age_str = f"{age_years} г. {age_rem_days} дн."
                else:
                    age_str = f"{age_rem_days} дн."

            days_left = bbu.get("real_remain_days", "N/A")
            age_str = str(bbu.get("age_days", "N/A")) if not isinstance(bbu.get("age_days"), int) else age_str

            values = [
                bbu.get("sys_name", ""),
                bbu.get("sys_model", ""),
                bbu.get("sys_serial", ""),
                bbu.get("id", ""),
                bbu.get("health", ""),
                bbu.get("running", ""),
                bbu.get("voltage", ""),
                bbu.get("remain_life_log", "N/A"),
                str(days_left),
                bbu.get("end_of_life", ""),
                bbu.get("delivered_on", ""),
                age_str,
                bbu.get("item", ""),
                bbu.get("barcode", "")
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                
                if col in (3, 4, 7, 8):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                self.table.setItem(row, col, item)

            self.apply_row_color(row, days_left)

        self.finalize_table()

    def get_export_data(self):
        """Возвращает данные для экспорта (вызывается из главного окна)."""
        return self._last_bbu_data