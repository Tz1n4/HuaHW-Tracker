#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export_Excel.py — генерация Excel-отчёта по форме ЗИП.

Класс ExcelExporter:
- берёт шаблон Form.xlsx (лежит рядом со скриптом),
- копирует его,
- заполняет лист "ЗИП" данными из парсера,
- сохраняет результат.

Режимы:
- export_single(sys_info, components, output_dir, name_hint)
      1 лог → 1 файл, 1 СХД внутри.

- export_batch(systems_data, output_dir, folder_name)
      N логов → 1 файл, N СХД внутри (batch).

Логика заполнения листа "ЗИП":
  Для каждой СХД i = 1, 2, 3...:
    1. Корневая строка (A = i):
         F = System Name
         G = Huawei
         H = Product Model
         I = Product Serial Number
         J = парт-номер оборудования (extract_part_number_from_serial)
         K = Description enclosure CTE0
         L = Storage
    2. Дочерние строки (A = i.1, i.2, ...) — уникальные BOM:
         K = name (Description или Vendor Model)
         L = категория по типу
         M = BOM (для SFP без BOM — пусто)
         N = комментарий (для SFP без BOM)
         O = количество таких компонентов
         P = 1
         R = =P{row}-Q{row}
    3. Memory (синтетическая, всегда):
         K = TEXT_MEMORY
         L = "Memory"
         P = 1
         R = =P{row}-Q{row}
    4. System Disk Drive (синтетическая, всегда последняя):
         K = TEXT_SYSTEM_DISK
         L = "System Disk Drive"
         P = 1
         R = =P{row}-Q{row}

Стили:
  - Корневая строка → копирует стиль со строки 2 шаблона.
  - Дочерние, Memory, SystemDisk → копируют стиль со строки 3 шаблона.
"""

import os
import re
import shutil
from copy import copy
from datetime import datetime

import openpyxl

from Utils.Utils_Constants import (
    TEMPLATE_PATH, SHEET_ZIP,
    COL_NO, COL_CUSTOMER, COL_PROJECT,
    COL_SYS_NAME, COL_VENDOR, COL_MODEL, COL_SN, COL_PART_HW,
    COL_ZIP_NAME, COL_ZIP_TYPE, COL_PART_ZIP, COL_COMMENT,
    COL_QTY_UNIT, COL_QTY_ZIP, COL_QTY_STOCK, COL_DELTA,
    ZIP_DATA_START_ROW,
    TYPE_TO_CATEGORY, ENCLOSURE_CTE_CATEGORY, ENCLOSURE_DAE_CATEGORY,
    TYPE_PRIORITY,
    TEXT_MEMORY, TEXT_SYSTEM_DISK, CATEGORY_SYSTEM_DISK, TEXT_SFP_NO_BOM_TEMPLATE,
    OUTPUT_NAME_TEMPLATE, TIMESTAMP_FORMAT,
    DEFAULT_VENDOR, DEFAULT_QTY_ZIP, DELTA_FORMULA_TEMPLATE,
)
from Utils.Utils_Regex_Helpers import (
    extract_part_number_from_serial,
    sanitize_for_excel,
)


def _is_real_bom(value):
    """True, если BOM начинается с цифры (например, '02355XAC')."""
    if not value:
        return False
    return bool(re.match(r'^\d', str(value)))


class ExcelExporter:
    """Формирует Excel-отчёт ЗИП по шаблону Form.xlsx."""

    def __init__(self, template_path=None):
        self.template_path = template_path or TEMPLATE_PATH
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

    # --------------------------------------------------------------------------
    # ПУБЛИЧНЫЙ API
    # --------------------------------------------------------------------------

    def export_single(self, sys_info, components, output_dir, name_hint,
                      include_synthetic=True, customer="", project=""):
        """Один лог → один файл."""
        return self.export_batch(
            systems_data=[(sys_info, components)],
            output_dir=output_dir,
            folder_name=name_hint,
            include_synthetic=include_synthetic,
            customer=customer,
            project=project,
        )

    def export_batch(self, systems_data, output_dir, folder_name,
                     include_synthetic=True, customer="", project=""):
        """N логов → 1 файл (N СХД внутри)."""
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        filename = OUTPUT_NAME_TEMPLATE.format(name=folder_name, timestamp=timestamp)
        output_path = os.path.join(output_dir, filename)

        shutil.copyfile(self.template_path, output_path)

        wb = openpyxl.load_workbook(output_path)
        ws = wb[SHEET_ZIP]

        systems_sorted = sorted(systems_data, key=lambda x: x[0].get("name", ""))

        current_row = ZIP_DATA_START_ROW
        for i, (sys_info, components) in enumerate(systems_sorted, start=1):
            current_row = self._fill_system(
                ws=ws,
                start_row=current_row,
                sys_index=i,
                sys_info=sys_info,
                components=components,
                include_synthetic=include_synthetic,
                customer=customer,
                project=project,
            )

        wb.save(output_path)
        return output_path

    # --------------------------------------------------------------------------
    # ВНУТРЕННИЕ МЕТОДЫ
    # --------------------------------------------------------------------------

    def _fill_system(self, ws, start_row, sys_index, sys_info, components,
                     include_synthetic=True, customer="", project=""):
        """Заполняет одну СХД. Возвращает следующую свободную строку."""
        row = start_row

        if row != 2:
            self._copy_style(ws, src_row=2, dst_row=row)
        self._write_root_row(ws, row, sys_index, sys_info, components,
                             customer=customer, project=project)
        row += 1

        child_rows = self._build_child_rows(components)
        for j, child in enumerate(child_rows, start=1):
            if row != 3:
                self._copy_style(ws, src_row=3, dst_row=row)
            self._write_child_row(
                ws=ws, row=row, sys_index=sys_index,
                child_index=j, sys_info=sys_info, child=child,
                customer=customer, project=project,
            )
            row += 1

        if include_synthetic:
            self._copy_style(ws, src_row=row - 1, dst_row=row)
            self._write_synthetic_row(
                ws=ws, row=row, sys_index=sys_index,
                child_index=len(child_rows) + 1, sys_info=sys_info,
                text=TEXT_MEMORY, category="Memory",
                customer=customer, project=project,
            )
            row += 1

            self._copy_style(ws, src_row=row - 1, dst_row=row)
            self._write_synthetic_row(
                ws=ws, row=row, sys_index=sys_index,
                child_index=len(child_rows) + 2, sys_info=sys_info,
                text=TEXT_SYSTEM_DISK, category=CATEGORY_SYSTEM_DISK,
                customer=customer, project=project,
            )
            row += 1

        return row

    # --------------------------------------------------------------------------
    # БЕЗОПАСНАЯ ЗАПИСЬ В ЯЧЕЙКУ
    # --------------------------------------------------------------------------

    def _set(self, ws, row, col, value):
        """Запись значения с санитизацией (удаление непечатаемых символов)."""
        ws.cell(row=row, column=col).value = sanitize_for_excel(value)

    # --------------------------------------------------------------------------
    # КОПИРОВАНИЕ СТИЛЯ
    # --------------------------------------------------------------------------

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

    # --------------------------------------------------------------------------
    # ЗАПИСЬ СТРОК
    # --------------------------------------------------------------------------

    def _write_common(self, ws, row, no_value, sys_info, customer, project):
        """Записывает общие для всех строк колонки: A, B, C, F, G, H."""
        self._set(ws, row, COL_NO, no_value)
        self._set(ws, row, COL_CUSTOMER, customer)
        self._set(ws, row, COL_PROJECT, project)
        self._set(ws, row, COL_SYS_NAME, sys_info.get("name", ""))
        self._set(ws, row, COL_VENDOR, DEFAULT_VENDOR)
        self._set(ws, row, COL_MODEL, sys_info.get("model", ""))

    def _write_root_row(self, ws, row, sys_index, sys_info, components,
                        customer="", project=""):
        """Корневая строка СХД (A = i, L = Storage)."""
        self._write_common(ws, row, sys_index, sys_info, customer, project)

        serial = sys_info.get("serial", "")
        self._set(ws, row, COL_SN, serial)
        self._set(ws, row, COL_PART_HW, extract_part_number_from_serial(serial))

        cte0_desc = self._find_cte0_description(components)
        self._set(ws, row, COL_ZIP_NAME, cte0_desc)
        self._set(ws, row, COL_ZIP_TYPE, ENCLOSURE_CTE_CATEGORY)

    def _write_child_row(self, ws, row, sys_index, child_index, sys_info, child,
                         customer="", project=""):
        """Дочерняя строка (одна строка = один уникальный BOM)."""
        no_value = f"{sys_index}.{child_index}"
        self._write_common(ws, row, no_value, sys_info, customer, project)

        self._set(ws, row, COL_ZIP_NAME, child["name"])
        self._set(ws, row, COL_ZIP_TYPE, child["category"])
        self._set(ws, row, COL_PART_ZIP, child["bom_for_M"])

        if child["comment"]:
            self._set(ws, row, COL_COMMENT, child["comment"])

        self._set(ws, row, COL_QTY_UNIT, child["count"])
        self._set(ws, row, COL_QTY_ZIP, DEFAULT_QTY_ZIP)
        self._set(ws, row, COL_DELTA, DELTA_FORMULA_TEMPLATE.format(row=row))

    def _write_synthetic_row(self, ws, row, sys_index, child_index, sys_info,
                             text, category, customer="", project=""):
        """Синтетическая строка (Memory или System Disk Drive)."""
        no_value = f"{sys_index}.{child_index}"
        self._write_common(ws, row, no_value, sys_info, customer, project)

        self._set(ws, row, COL_ZIP_NAME, text)
        self._set(ws, row, COL_ZIP_TYPE, category)
        self._set(ws, row, COL_QTY_ZIP, DEFAULT_QTY_ZIP)
        self._set(ws, row, COL_DELTA, DELTA_FORMULA_TEMPLATE.format(row=row))

    # --------------------------------------------------------------------------
    # ПОДГОТОВКА ДОЧЕРНИХ СТРОК
    # --------------------------------------------------------------------------

    def _build_child_rows(self, components):
        """Группирует компоненты по (type, bom), сортирует по приоритету."""
        children = []
        for comp in components:
            if comp.get("type") == "Enclosure" and comp.get("id", "").startswith("CTE"):
                continue
            children.append(comp)

        grouped = {}
        for comp in children:
            comp_type = comp.get("type", "")
            bom = comp.get("bom", "")
            comp_id = comp.get("id", "")

            if not bom or bom == "N/A":
                continue

            key = (comp_type, bom)
            if key not in grouped:
                grouped[key] = {
                    "type": comp_type,
                    "name": comp.get("name", ""),
                    "bom":  bom,
                    "id":   comp_id,
                    "count": 0,
                }
            grouped[key]["count"] += 1

        result = []
        for (comp_type, bom), grp in grouped.items():
            if comp_type == "Enclosure":
                enc_id = grp.get("id", "")
                if enc_id.startswith("DAE"):
                    category = ENCLOSURE_DAE_CATEGORY
                    priority = TYPE_PRIORITY["Enclosure_DAE"]
                elif enc_id.startswith("CTE"):
                    category = ENCLOSURE_CTE_CATEGORY
                    priority = TYPE_PRIORITY.get("Enclosure", 15)
                else:
                    category = TYPE_TO_CATEGORY.get(comp_type, comp_type)
                    priority = TYPE_PRIORITY.get(comp_type, 999)
            else:
                category = TYPE_TO_CATEGORY.get(comp_type, comp_type)
                priority = TYPE_PRIORITY.get(comp_type, 999)

            bom_for_M, comment = self._get_M_and_N(comp_type, grp["name"], bom)

            result.append({
                "name":      grp["name"],
                "category":  category,
                "bom_for_M": bom_for_M,
                "comment":   comment,
                "count":     grp["count"],
                "priority":  priority,
                "bom":       bom,
            })

        result.sort(key=lambda x: (x["priority"], x["bom"]))
        return result

    # --------------------------------------------------------------------------
    # ЛОГИКА M/N (Part Number + комментарий)
    # --------------------------------------------------------------------------

    def _get_M_and_N(self, comp_type, name, bom):
        """Возвращает (M_value, N_comment)."""
        if _is_real_bom(bom):
            return (bom, "")

        if comp_type == "SFP Module":
            parts = bom.split(" ", 1)
            vendor = parts[0] if parts else ""
            model = parts[1] if len(parts) > 1 else ""
            comment = TEXT_SFP_NO_BOM_TEMPLATE.format(vendor=vendor, model=model)
            return ("", comment)

        return (bom, "")

    # --------------------------------------------------------------------------
    # ПОИСК CTE0
    # --------------------------------------------------------------------------

    def _find_cte0_description(self, components):
        """Ищет Description enclosure CTE0."""
        for comp in components:
            if comp.get("type") == "Enclosure" and comp.get("id") == "CTE0":
                return comp.get("name", "")
        return ""