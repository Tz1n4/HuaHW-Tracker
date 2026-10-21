#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core_System_Info.py — разбор шапки лога и определение версии системы.

Парсит блок SUMMARY из лога Huawei Storage и возвращает словарь:
    {
        "name":    str,   # System Name
        "serial":  str,   # Product Serial Number
        "model":   str,   # Product Model
        "version": str,   # "V6" / "V7" / "V5" / "V3" / "Unknown"
    }

Приоритет определения версии:
    1) по Product Model (например, "OceanStor Dorado 8000 V6" → V6)
    2) по Product Version (например, "V600R005C27" → V6)
    3) по содержимому (маркеры "Control Board(", "Controller ID:" и т.д.)

Поддерживаемые версии — см. Utils_Constants.SUPPORTED_VERSIONS.
"""

import re


# ==============================================================================
# 1. БАЗОВЫЙ ПАРСИНГ ПОЛЕЙ ШАПКИ
# ==============================================================================

def parse_system_info(content):
    """
    Извлекает поля System Name, Serial, Model, Version из содержимого лога.

    Возвращает dict с ключами: name, serial, model, version.
    Все поля гарантированно присутствуют (значение "N/A" при отсутствии).
    """
    m = re.search(r'System Name:\s*(.+)', content)
    name = m.group(1).strip() if m else "N/A"

    m = re.search(r'Product Serial Number:\s*(.+)', content)
    serial = m.group(1).strip() if m else "N/A"

    m = re.search(r'Product Model:\s*(.+)', content)
    model = m.group(1).strip() if m else "N/A"

    m = re.search(r'Product Version:\s*(.+)', content)
    fw = m.group(1).strip() if m else ""

    m = re.search(r'System Location:\s*(.+)', content)
    location = m.group(1).strip() if m else "N/A"

    version = detect_version(model=model, fw=fw, content=content)

    return {
        "name":     name,
        "serial":   serial,
        "model":    model,
        "location": location,
        "fw":       fw,
        "version":  version,
    }


# ==============================================================================
# 2. ОПРЕДЕЛЕНИЕ ВЕРСИИ СИСТЕМЫ
# ==============================================================================

def detect_version(model, fw, content):
    """
    Определяет версию системы по трём источникам (в порядке приоритета):

    1) Product Model:
         "OceanStor Dorado 8000 V6"   → "V6"
         "OceanStor 5500 V5"          → "V5"

    2) Product Version:
         "V600R005C27"                → "V6"
         "V500R007C20"                → "V5"

    3) Содержимое:
         "Control Board("             → "V6"
         "Controller ID:" + "sfp info:" → "V3"
         "Controller ID:"             → "V5"

    Возвращает строку вида "V6", "V5", "V3", "V7" или "Unknown".
    Если версия известна (например, "V7"), но не поддерживается —
    всё равно возвращаем её; отклонение произойдёт в Core_Base_Parser.
    """
    if model and model != "N/A":
        m = re.search(r'\bV(\d)\b', model)
        if m:
            return f"V{m.group(1)}"

    if fw:
        m = re.match(r'^V(\d)', fw.strip())
        if m:
            return f"V{m.group(1)}"

    if "Control Board(" in content:
        return "V6"

    if (
        "Enclosure Info" in content
        and "Electronic Label" in content
        and "Controller ID:" in content
    ):
        return "V5"

    if "Controller ID:" in content and "sfp info:" in content:
        return "V3"
    if "Controller ID:" in content:
        return "V5"

    return "Unknown"