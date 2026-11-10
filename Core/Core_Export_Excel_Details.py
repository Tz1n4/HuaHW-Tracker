#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core_Export_Excel_Details.py — генерация Excel-отчёта по детальному анализу.
"""

import os
import shutil
from datetime import datetime
from copy import copy

import openpyxl

from Utils.Utils_Constants import (
    DETAILS_TEMPLATE_PATH,
    TIMESTAMP_FORMAT,
)
from Utils.Utils_Regex_Helpers import sanitize_for_excel


class DetailsExcelExporter:
    """Формирует Excel-отчёт по детальному анализу компонентов."""

    def __init__(self, template_path=None):
        self.template_path = template_path or DETAILS_TEMPLATE_PATH
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

    def export_all(self, components_data, output_dir, name_hint):
        """
        Экспортирует данные всех выбранных компонентов в ОДИН файл.
        
        :param components_data: Словарь {имя_листа: список_словарей}
                                Пример: {"BBU": [...], "Controller": [...]}
        :param output_dir: Куда сохранять
        :param name_hint: Имя файла (без расширения и метки времени)
        """
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        filename = f"Детальный_анализ_{name_hint}_{timestamp}.xlsx"
        output_path = os.path.join(output_dir, filename)

        shutil.copyfile(self.template_path, output_path)
        wb = openpyxl.load_workbook(output_path)

        for sheet_name, data in components_data.items():
            if not data:
                continue
            
            if sheet_name not in wb.sheetnames:
                print(f"Предупреждение: лист '{sheet_name}' отсутствует в шаблоне. Пропуск.")
                continue

            ws = wb[sheet_name]
            self._fill_sheet(ws, data, sheet_name)

        wb.save(output_path)
        return output_path

    def _fill_sheet(self, ws, data, sheet_name):
        """Заполняет конкретный лист данными."""
        current_row = 2
        
        # Карта правил: какой ключ из словаря в какую колонку Excel писать
        # Начинается с 5 (колонка E), так как A, B, C, D общие.
        writers_map = self._get_writers_map(sheet_name)

        for i, item in enumerate(data, start=1):
            if current_row > 2:
                self._copy_style(ws, src_row=2, dst_row=current_row)

            # Заполняем A, B, C, D
            self._set(ws, current_row, 1, i)
            self._set(ws, current_row, 2, item.get("sys_name", ""))
            self._set(ws, current_row, 3, item.get("sys_model", ""))
            self._set(ws, current_row, 4, item.get("sys_serial", ""))

            # Заполняем уникальные колонки (E и далее)
            for col_idx, writer in writers_map.items():
                if callable(writer):
                    val = writer(item)
                else:
                    val = item.get(writer, "")
                self._set(ws, current_row, col_idx, val)

            current_row += 1

    def _get_writers_map(self, sheet_name):
        """Возвращает карту колонок и ключей данных для конкретного листа."""
        if sheet_name == "Controller":
            return {
                5: "id",             # E: ID (Слот)
                6: "health",         # F: Здоровье
                7: "running",        # G: Статус
                8: "barcode",        # H: Серийный номер запчасти
                9: "item",           # I: Part Number
                10: "desc",          # J: Наименование запчасти
                11: "cache_cap",     # K: Cache Capacity
                12: "manufactured",  # L: Дата производства
                13: "cpu"            # M: CPU
            }
        elif sheet_name == "BBU":
            return {
                5: "id",             # E: ID (Слот)
                6: "health",         # F: Здоровье
                7: "running",        # G: Статус
                8: "voltage",        # H: Напряжение
                9: "remain_life_log",# I: Остаток (дн. из лога)
                10: "real_remain_days", # J: Остаток на сегодня (дн.)
                11: "end_of_life",   # K: Конец срока
                12: "delivered_on",  # L: Поставка
                13: lambda b: self._format_age(b.get("age_days")), # M: Возраст
                14: "item",          # N: Part Number
                15: "barcode"        # O: Серийный номер запчасти
            }
        # Сюда будем добавлять остальные компоненты по мере готовности
        return {}

    def _format_age(self, age_days):
        """Вспомогательный метод для форматирования возраста."""
        if isinstance(age_days, int):
            age_years = age_days // 365
            age_rem_days = age_days % 365
            if age_years > 0:
                return f"{age_years} г. {age_rem_days} дн."
            else:
                return f"{age_rem_days} дн."
        return "N/A"

    def _set(self, ws, row, col, value):
        """Запись значения с санитизацией."""
        ws.cell(row=row, column=col).value = sanitize_for_excel(value)

    def _copy_style(self, ws, src_row, dst_row):
        """Копирует стиль всех ячеек из src_row в dst_row."""
        total_cols = ws.max_column
        for col in range(1, total_cols + 1):
            src = ws.cell(row=src_row, column=col)
            dst = ws.cell(row=dst_row, column=col)
            dst.font = copy(src.font)
            dst.border = copy(src.border)
            dst.fill = copy(src.fill)
            dst.alignment = copy(src.alignment)
            dst.number_format = src.number_format
            dst.protection = copy(src.protection)