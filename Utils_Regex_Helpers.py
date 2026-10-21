#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils_Regex_Helpers.py — общие утилиты для работы со строками и regex.

Содержит:
- extract_label_fields: разбор блока Electronic Label (Description, BarCode, Item).
- extract_part_number_from_serial: извлечение парт-номера оборудования из серийника.
- extract_bom_from_serial: извлечение BOM из SN (правило Huawei: SN[2:10]).
- make_name_from_label: Description или заглушка.
- make_bom_from_label_or_serial: BOM из Elabel или из SN.
- sanitize_for_excel: очистка строки для записи в Excel.
"""

import re


# ==============================================================================
# 1. РАЗБОР ELECTRONIC LABEL
# ==============================================================================

def extract_label_fields(block_text):
    """Извлекает поля из блока Electronic Label: Description, BarCode, Item."""
    if not block_text:
        return {"description": "N/A", "barcode": "N/A", "item": "N/A"}

    desc_m = re.search(r'Description=(.+?)(?:\n|$)', block_text)
    barcode_m = re.search(r'BarCode=(\S+)', block_text)
    item_m = re.search(r'Item=(\S+)', block_text)

    return {
        "description": desc_m.group(1).strip() if desc_m else "N/A",
        "barcode": barcode_m.group(1).strip() if barcode_m else "N/A",
        "item": item_m.group(1).strip() if item_m else "N/A",
    }


# ==============================================================================
# 2. ИЗВЛЕЧЕНИЕ PART NUMBER ОБОРУДОВАНИЯ ИЗ СЕРИЙНИКА
# ==============================================================================

def extract_part_number_from_serial(serial):
    """
    Извлекает part number оборудования из SN (8 символов с 3-й позиции).
    Например: '2102350ABC10XX000001' → '02350ABC'.
    """
    if not serial or len(serial) < 10:
        return "N/A"
    return serial[2:10]


# ==============================================================================
# 3. САНИТИЗАЦИЯ ДЛЯ EXCEL
# ==============================================================================

_ILLEGAL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

_HTML_ESCAPE_MAP = {
    "&amp;":  "&",
    "&lt;":   "<",
    "&gt;":   ">",
    "&quot;": '"',
    "&#39;":  "'",
    "&apos;": "'",
}


def sanitize_for_excel(value):
    """Убирает управляющие символы и раскрывает HTML-escape."""
    if value is None:
        return ""
    if not isinstance(value, str):
        return value

    value = _ILLEGAL_CHARS_RE.sub("", value)
    for entity, char in _HTML_ESCAPE_MAP.items():
        value = value.replace(entity, char)
    return value


# ==============================================================================
# 4. ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ (для V3)
# ==============================================================================

def extract_bom_from_serial(serial):
    """
    Извлекает BOM из SN, если SN похож на серийник Huawei.
    Правило: BOM = SN[2:10], если SN начинается с "21" или "03".
    """
    if not serial or len(serial) < 10:
        return "N/A"
    if serial[0:2] not in ("21", "03"):
        return "N/A"
    return serial[2:10]


def make_name_from_label(lbl, fallback_text="N/A"):
    """Возвращает Description из Elabel или заглушку."""
    if lbl.get("description") and lbl["description"] != "N/A":
        return lbl["description"]
    return fallback_text


def make_bom_from_label_or_serial(lbl, serial=None):
    """Возвращает BOM: сначала из Elabel (Item), потом из SN."""
    if lbl.get("item") and lbl["item"] != "N/A":
        return lbl["item"]
    bom = extract_bom_from_serial(serial)
    return bom if bom != "N/A" else "N/A"