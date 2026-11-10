#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Details_Controller_Tab.py — вкладка детального анализа Controller.
"""

import os
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt

from GUI.Gui_Dialogs.Gui_Details_Tabs.Gui_Details_Base_Tab import BaseDetailsTab
from Parsers.Parsers_Details.Parser_Controller_Details import parse_controller_details
from Core.Core_System_Info import parse_system_info


class ControllerDetailsTab(BaseDetailsTab):
    """Вкладка с детальной информацией по контроллерам."""

    def __init__(self, file_paths, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self._last_data = []
        
        headers = [
            "Система", "Модель СХД", "Серийный номер СХД", "ID (Слот)", 
            "Здоровье", "Статус", "Серийный номер запчасти", "Part Number", 
            "Наименование запчасти", "Cache Capacity", "Дата производства", "CPU"
        ]
        self.setup_columns(headers)
        
        self._load_data()

    def _load_data(self):
        all_data = []
        
        for fpath in self.file_paths:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                sys_info = parse_system_info(content[:5000])
                sys_name = sys_info.get("name", os.path.basename(fpath))
                sys_model = sys_info.get("model", "N/A")
                sys_version = sys_info.get("version", "V3")
                sys_serial = sys_info.get("serial", "N/A")
                
                ctrl_list = parse_controller_details(content, sys_version=sys_version)
                
                for ctrl in ctrl_list:
                    ctrl["sys_name"] = sys_name
                    ctrl["sys_model"] = sys_model
                    ctrl["sys_serial"] = sys_serial
                    all_data.append(ctrl)
            except Exception as e:
                print(f"Ошибка при чтении {fpath}: {e}")

        self._last_data = all_data
        self._populate_table()

    def _populate_table(self):
        if not self._last_data:
            return

        self.table.setRowCount(len(self._last_data))
        
        for row, ctrl in enumerate(self._last_data):
            values = [
                ctrl.get("sys_name", ""),
                ctrl.get("sys_model", ""),
                ctrl.get("sys_serial", ""),
                ctrl.get("id", ""),
                ctrl.get("health", ""),
                ctrl.get("running", ""),
                ctrl.get("barcode", ""),
                ctrl.get("item", ""),
                ctrl.get("desc", ""),
                ctrl.get("cache_cap", ""),
                ctrl.get("manufactured", ""),
                ctrl.get("cpu", ""),
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                
                if col in (3, 4, 5):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                self.table.setItem(row, col, item)

        self.finalize_table()

    def get_export_data(self):
        """Возвращает данные для экспорта."""
        return self._last_data