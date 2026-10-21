#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Equipment_Detail_Export.py — «Детализация оборудования» (BBU).

Модуль парсит секцию "BBU Info----..." лога Huawei Storage (V3/V5/V6)
и формирует Excel-отчёт с детальной информацией по каждому BBU.

Ключевые особенности:
- Универсальный парсер блоков BBU для трёх структур логов:
    V3 Dorado / OceanStor : "BBU ID: CTE0.0"
    V5 flat/nested        : "ID: CTE0.A.BBU" / "BBU ID: ..."
    V6                    : "BBU(CTE0.A.BBU)-----------"
  (regex-паттерны взяты за основу из Parser_V3/V5/V6.parse_bbu, но
   здесь дополнительно извлекаются Health/Running Status, Voltage,
   Firmware Version, BarCode, Description, Delivered On, Manufactured=,
   RemainLife(days)).

- ДИНАМИЧЕСКИЙ РАСЧЁТ СРОКА СЛУЖБЫ (RemainLife):
    Статическое значение RemainLife(days) из лога ИГНОРИРУЕТСЯ.
    1) Дата создания лога берётся из первой строки:
         "PROFILE FOR STORAGE ARRAY: <name> (YYYY-M-D HH:MM:SS)"
    2) days_since = (datetime.now() - log_date).days
    3) Actual_RemainLife = Static_RemainLife - days_since
    4) Если результат < 0 → "Expired".

Точка входа: export_equipment_detail(log_path, output_xlsx).
"""

import os
import re
from datetime import datetime

import openpyxl
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill

from Core_System_Info import parse_system_info
from Utils_Regex_Helpers import extract_label_fields, sanitize_for_excel


# ==============================================================================
# 1. ПАРСИНГ ДАТЫ СОЗДАНИЯ ЛОГА
# ==============================================================================

_LOG_DATE_RE = re.compile(
    r'PROFILE\s+FOR\s+STORAGE\s+ARRAY:.*?\((\d{4}-\d{1,2}-\d{1,2})\s+(\d{1,2}:\d{2}:\d{2})\)',
    re.IGNORECASE,
)


def parse_log_date(content):
    """
    Извлекает дату создания лога из строки
    "PROFILE FOR STORAGE ARRAY: ... (YYYY-M-D HH:MM:SS)".

    :return: datetime или None, если дата не найдена.
    """
    head = content[:4000]  # строка PROFILE всегда в самом начале лога
    m = _LOG_DATE_RE.search(head)
    if not m:
        return None
    try:
        return datetime.strptime(
            f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        return None


# ==============================================================================
# 2. УНИВЕРСАЛЬНЫЙ ПАРСЕР БЛОКОВ BBU (V3 / V5 / V6)
# ==============================================================================

# Паттерны начала блока BBU для разных версий (по мотивам Parser_V*.parse_bbu).
_BBU_BLOCK_PATTERNS = [
    # V6: BBU(CTE0.A.BBU)----------- / BBU(CTE0.BBU1)-----------
    re.compile(
        r'BBU\(((?:CTE\d+\.(?:[A-Z]\.BBU|BBU\d+)))\)-+\n(.*?)'
        r'(?=\s*BBU\((?:CTE\d+\.(?:[A-Z]\.BBU|BBU\d+))\)|\n[A-Z][A-Za-z ]+-{5,}|\Z)',
        re.DOTALL,
    ),
    # V5: "ID: CTE0.A.BBU" / "BBU ID: CTE0.BBU1" и т.п.
    re.compile(
        r'(?:^|\n)\s*(?:BBU )?ID:\s*'
        r'((?:CTE)\d+(?:\.(?:[A-Z]\.BBU|BBU\d+|\d+|[A-Z]\.\d+|PSU\d+)))\s*\n(.*?)'
        r'(?=\n\s*(?:BBU )?ID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)',
        re.DOTALL,
    ),
    # V3 Dorado: "BBU ID: CTE0.0"
    re.compile(
        r'BBU ID:\s*([A-Z]+\d+\.\d+)\s*\n(.*?)'
        r'(?=\n\s*BBU ID:|\n[A-Za-z][A-Za-z ]*-{5,}|\Z)',
        re.DOTALL,
    ),
]


def _field(block, name):
    """Достаёт поле вида 'Name : value' из блока."""
    m = re.search(rf'^\s*{re.escape(name)}\s*:\s*(.+?)\s*$', block, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _elabel_field(block, name):
    """Достаёт поле вида 'Name= value' / 'Name=value' из Electronic Label."""
    m = re.search(rf'{re.escape(name)}=\s*(\S+)', block)
    return m.group(1).strip() if m else ""


# Совместимость с Utils_Regex_Helpers.extract_label_fields: форматы логов
# Huawei содержат варианты как "BarCode=XXX", так и "BarCode= XXX"
# (пробел после "="). Паттерны без \s* такие поля пропускают, поэтому в
# модуле используются собственные regex с учётом обоих вариантов.
_ITEM_RE      = re.compile(r'Item=(\S+)')
_BARCODE_RE   = re.compile(r'BarCode=(\S+)')
_DESCRIBE_RE  = re.compile(r'Description=(.+?)(?:\n|$)')


def _lbl_value(lbl_dict, key, lbl_block, tag):
    """Значение поля Elabel: сначала стандартный extract_label_fields,
    затем fallback-regex, допускающий пробел после '='."""
    val = lbl_dict.get(key, "N/A")
    if val and val != "N/A":
        return val
    return _elabel_field(lbl_block, tag)


def parse_bbu_details(content):
    """
    Универсально парсит все блоки BBU из содержимого лога (V3/V5/V6).

    :return: список dict с ключами:
        enclosure_id, bbu_id, health_status, running_status, voltage,
        firmware_version, barcode, description, part_number,
        delivered_on, manufactured_on, remain_life_static.
    """
    records = []
    seen_ids = set()

    for pattern in _BBU_BLOCK_PATTERNS:
        for m in pattern.finditer(content):
            bbu_id = m.group(1).strip()
            if bbu_id in seen_ids:
                continue

            block = m.group(2)

            # Enclosure ID: либо из поля лога, либо из ID (CTE0.x.y → CTE0)
            enclosure_id = _field(block, "Enclosure ID")
            if not enclosure_id:
                em = re.match(r'(CTE\d+)', bbu_id)
                enclosure_id = em.group(1) if em else ""

            # Электронная этикетка: BarCode / Description / Manufactured= / Item(PN)
            # Разделители конца блока различаются между версиями журналов:
            #   V3 Dorado  : следующий "BBU ID:"
            #   V5 flat    : следующий "(BBU )?ID:"
            #   V6         : следующий "BBU(...)" или заголовок секции "---"
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)'
                r'(?=\n\s*(?:BBU )?ID:|\n\s*BBU\(|\n[^\nD][^\n]*?-{5,}|\Z)',
                block, re.DOTALL,
            )
            lbl_block = (elabel_m.group(1) if elabel_m else block).strip()
            lbl = extract_label_fields(lbl_block)

            barcode = _lbl_value(lbl, "barcode", lbl_block, "BarCode")
            description = _lbl_value(lbl, "description", lbl_block, "Description")
            manufactured = _elabel_field(lbl_block, "Manufactured")
            # Part Number: Item= из Elabel; если отсутствует — пусто (требование ТЗ)
            part_number = _lbl_value(lbl, "item", lbl_block, "Item")

            # Пропускаем полностью пустые блоки (не BBU-детали)
            if not any([barcode, description, _field(block, "Health Status"),
                        _field(block, "RemainLife(days)")]):
                continue

            seen_ids.add(bbu_id)

            remain_raw = _field(block, "RemainLife(days)")
            try:
                remain_static = int(re.sub(r'[^\d-]', '', remain_raw) or "")
            except ValueError:
                remain_static = None

            records.append({
                "enclosure_id":     enclosure_id,
                "bbu_id":           bbu_id,
                "health_status":    _field(block, "Health Status"),
                "running_status":   _field(block, "Running Status"),
                "voltage":          _field(block, "Voltage(V)"),
                "firmware_version": (_field(block, "Firmware Version")
                                     or _elabel_field(block, "Software Version")),
                "barcode":          barcode,
                "description":      description,
                "part_number":      part_number,
                "delivered_on":     _field(block, "Delivered On"),
                "manufactured_on":  manufactured,
                "remain_life_static": remain_static,
            })

    return records


# ==============================================================================
# 3. РАСЧЁТ АКТИУАЛЬНОГО RemainLife
# ==============================================================================

STATUS_EXPIRED = "Expired"


def calculate_actual_remainlife(static_remain_life, log_date, now=None):
    """
    Динамический расчёт остатка срока службы BBU.

    Actual_RemainLife = Static_RemainLife_from_Log - Days_Since_Log_Creation.
    Если результат < 0 → STATUS_EXPIRED.

    :param static_remain_life: int|None — RemainLife(days) из лога.
    :param log_date: datetime|None — дата создания лога.
    :param now: datetime — текущее время (для тестов можно передать явно).
    :return: int (дни) либо str STATUS_EXPIRED либо None (нет данных).
    """
    if static_remain_life is None or log_date is None:
        return None

    if now is None:
        now = datetime.now()

    days_since = (now - log_date).days
    if days_since < 0:
        days_since = 0

    actual = static_remain_life - days_since
    if actual < 0:
        return STATUS_EXPIRED
    return actual


# ==============================================================================
# 4. ГЕНЕРАЦИЯ EXCEL-ОТЧЁТА
# ==============================================================================

# Заголовки колонок отчёта
COLUMNS = [
    ("Enclosure ID",        14),
    ("BBU ID",              16),
    ("Health Status",       14),
    ("Running Status",      16),
    ("Voltage(V)",          12),
    ("Firmware Version",    16),
    ("Part Number",         14),
    ("BarCode",             22),
    ("Description",         32),
    ("Delivered On",        18),
    ("Manufactured",        14),
    ("RemainLife (log, days)", 18),
    ("Days Since Log",      15),
    ("Actual RemainLife (days)", 20),
]

_SHEET_TITLE = "Детализация оборудования (BBU)"

_thin_side = Side(style="thin")
_BORDER = Border(left=_thin_side, right=_thin_side, top=_thin_side, bottom=_thin_side)
_HEADER_FONT = Font(bold=True)
_TITLE_FONT = Font(bold=True, size=12)
_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
_HEADER_FILL = PatternFill("solid", fgColor="DDEBF7")


def write_report(records, output_xlsx, sys_info=None, log_date=None,
                 days_since_log=0, now=None):
    """
    Пишет список словарей-записей BBU в Excel-файл с базовой стилизацией
    (жирные заголовки, границы ячеек — аналогично Form.xlsx).

    :return: путь к созданному файлу.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BBU Detail"

    n_cols = len(COLUMNS)

    # --- Строка 1: заголовок отчёта ---
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
    title_cell = ws.cell(row=1, column=1, value=_SHEET_TITLE)
    title_cell.font = _TITLE_FONT
    title_cell.alignment = _CENTER

    # --- Строка 2: метаданные (модель / версия / дата лога) ---
    meta_parts = []
    if sys_info:
        model = sys_info.get("model", "N/A")
        version = sys_info.get("version", "N/A")
        name = sys_info.get("name", "N/A")
        meta_parts.append(f"System: {name} | Model: {model} | Version: {version}")
    if log_date is not None:
        meta_parts.append(f"Log created: {log_date.strftime('%Y-%m-%d %H:%M:%S')}")
    if meta_parts:
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n_cols)
        meta_cell = ws.cell(row=2, column=1, value=" || ".join(meta_parts))
        meta_cell.alignment = Alignment(horizontal="left", vertical="center")

    header_row = 3

    # --- Строка 3: заголовки колонок ---
    for idx, (title, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=header_row, column=idx, value=title)
        cell.font = _HEADER_FONT
        cell.border = _BORDER
        cell.alignment = _CENTER
        cell.fill = _HEADER_FILL
        ws.column_dimensions[cell.column_letter].width = width

    # --- Данные ---
    if now is None:
        now = datetime.now()

    for i, rec in enumerate(records):
        row = header_row + 1 + i
        actual = calculate_actual_remainlife(
            rec.get("remain_life_static"), log_date, now=now
        )

        static_val = rec.get("remain_life_static")
        values = [
            rec.get("enclosure_id", ""),
            rec.get("bbu_id", ""),
            rec.get("health_status", ""),
            rec.get("running_status", ""),
            rec.get("voltage", ""),
            rec.get("firmware_version", ""),
            rec.get("part_number", ""),   # без Part Number — пусто
            rec.get("barcode", ""),
            rec.get("description", ""),
            rec.get("delivered_on", ""),
            rec.get("manufactured_on", ""),
            static_val if static_val is not None else "",
            days_since_log,
            actual if actual is not None else "N/A",
        ]

        for col_idx, val in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col_idx,
                           value=sanitize_for_excel(val))
            cell.border = _BORDER
            cell.alignment = Alignment(horizontal="center", vertical="center")

    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

    out_dir = os.path.dirname(os.path.abspath(output_xlsx))
    os.makedirs(out_dir, exist_ok=True)
    wb.save(output_xlsx)
    return output_xlsx


# ==============================================================================
# 5. ТОЧКА ВХОДА
# ==============================================================================

def read_log_content(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def export_equipment_detail(log_path, output_xlsx=None, now=None):
    """
    Полный цикл: лог → парсинг BBU → расчёт RemainLife → Excel.

    :param log_path: путь к текстовому логу Huawei Storage.
    :param output_xlsx: путь к выходному Excel-файлу;
                        по умолчанию — рядом с логом
                        (<имя_лога>_Equipment_Detail.xlsx).
    :param now: datetime (опционально, для тестов).
    :return: dict {"output": path, "records": [...], "log_date": dt,
                   "days_since_log": int}
    """
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")

    if output_xlsx is None:
        base, _ = os.path.splitext(log_path)
        output_xlsx = f"{base}_Equipment_Detail.xlsx"

    if now is None:
        now = datetime.now()

    content = read_log_content(log_path)
    sys_info = parse_system_info(content)
    log_date = parse_log_date(content)

    days_since_log = 0
    if log_date is not None:
        days_since_log = max((now - log_date).days, 0)

    records = parse_bbu_details(content)

    write_report(records, output_xlsx, sys_info=sys_info,
                 log_date=log_date, days_since_log=days_since_log, now=now)

    return {
        "output": output_xlsx,
        "records": records,
        "sys_info": sys_info,
        "log_date": log_date,
        "days_since_log": days_since_log,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python Equipment_Detail_Export.py <log.txt> [output.xlsx]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    result = export_equipment_detail(sys.argv[1], out)
    print(f"Report written: {result['output']}")
    print(f"BBU records: {len(result['records'])}, "
          f"log date: {result['log_date']}, "
          f"days since log: {result['days_since_log']}")
