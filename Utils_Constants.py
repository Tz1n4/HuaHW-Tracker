#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils_Constants.py — общие константы проекта Huawei Storage Log Parser.

Содержит:
- Версию парсера и поддерживаемые версии СХД.
- Имя файла-шаблона Excel.
- Имена листов и индексы колонок формы ЗИП.
- Маппинг: тип компонента → категория ЗИП (колонка L).
- Приоритеты сортировки дочерних строк.
- Тексты-заглушки (Memory, SFP без BOM).
- Формат имён выходных файлов.
- Значения по умолчанию и шаблон формулы.
"""

import os


# ==============================================================================
# 1. ОБЩИЕ СВЕДЕНИЯ О ПАРСЕРЕ
# ==============================================================================

PARSER_VERSION = "18.0"
PARSER_NAME = "Huawei Storage Log Parser"

SUPPORTED_VERSIONS_DESCRIPTION = {
    "V3": "OceanStor 5300 / 5500 / 5600, OceanStor Dorado 5000 / 6000",
    "V5": "OceanStor 2600 / 5110 / 5210 / 5300 / 5500 / 5600 V5",
    "V6": "OceanStor Dorado 3000 / 5000 / 6000 / 8000",
}

SUPPORTED_VERSIONS = tuple(SUPPORTED_VERSIONS_DESCRIPTION.keys())

GUI_WINDOW_TITLE_TEMPLATE = "{name} - GUI v{version}"


# ==============================================================================
# ПОЛЕЗНЫЕ ССЫЛКИ (для меню Help -> Useful Links)
# ==============================================================================

USEFUL_LINKS = [
    (
        "Huawei Spare Parts Query",
        "https://info.support.huawei.com/storage/spareparts/#/home",
    ),
    (
        "Maintenance Status",
        "https://support.huawei.com/enterprise/ecareWechat",
    ),
]


# ==============================================================================
# 2. ФАЙЛ-ШАБЛОН EXCEL
# ==============================================================================

TEMPLATE_FILE = "Form.xlsx"

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), TEMPLATE_FILE)


# ==============================================================================
# 3. ЛИСТЫ EXCEL
# ==============================================================================

SHEET_EMPTY = "Лист2"
SHEET_ZIP = "ЗИП"


# ==============================================================================
# 4. ИНДЕКСЫ КОЛОНОК ФОРМЫ ЗИП (1-based, как в openpyxl)
# ==============================================================================

COL_NO          = 1     # A  — п/п
COL_CUSTOMER    = 2     # B  — Заказчик в CRM2
COL_PROJECT     = 3     # C  — Проект CRM2
COL_CITY        = 4     # D  — Локация оборудования ГОРОД
COL_ADDRESS     = 5     # E  — Локация оборудования АДРЕС
COL_SYS_NAME    = 6     # F  — Наименование оборудования по спецификации Заказчика
COL_VENDOR      = 7     # G  — Вендор оборудования согласно CRM2
COL_MODEL       = 8     # H  — Модель оборудования согласно CRM2
COL_SN          = 9     # I  — Серийный номер оборудования
COL_PART_HW     = 10    # J  — Артикул (part number) оборудования
COL_ZIP_NAME    = 11    # K  — Наименование ЗИП с техническими характеристиками
COL_ZIP_TYPE    = 12    # L  — Тип ЗИП согласно CRM2
COL_PART_ZIP    = 13    # M  — Part Number ЗИП
COL_COMMENT     = 14    # N  — Комментарий (аналоги и прочее)
COL_QTY_UNIT    = 15    # O  — Количество на ЕДИНИЦУ
COL_QTY_ZIP     = 16    # P  — Необходимо в ЗИП
COL_QTY_STOCK   = 17    # Q  — Кол-во на складах
COL_DELTA       = 18    # R  — Отклонение (=P-Q)
COL_QTY_BUY     = 19    # S  — Количество в Закуп
COL_REASON      = 20    # T  — Основание для Закупа

ZIP_DATA_START_ROW = 2


# ==============================================================================
# 5. МАППИНГ: ТИП КОМПОНЕНТА → КАТЕГОРИЯ ЗИП (колонка L)
# ==============================================================================

TYPE_TO_CATEGORY = {
    "Enclosure":        "Storage",
    "Controller":       "Controller",
    "Disk":             "Disk Drive",
    "Power Supply":     "Блок Питания",
    "BBU":              "Батарея",
    "Fan":              "Fan",
    "I/O Module":       "I/O Module",
    "Expansion Board":  "Expansion Board",
    "SFP Module":       "SFP",
    "Memory":           "Memory",
    "Data Switch":      "Data Switch",
}

ENCLOSURE_CTE_CATEGORY = "Storage"
ENCLOSURE_DAE_CATEGORY = "Disk Enclosure"

TYPE_PRIORITY = {
    "Controller":        10,
    "Disk":              20,
    "Enclosure_DAE":     30,
    "Data Switch":       35,
    "Power Supply":      40,
    "BBU":               50,
    "Fan":               60,
    "I/O Module":        70,
    "Expansion Board":   80,
    "SFP Module":        90,
    "Memory":            95,
    "System Disk Drive": 100,
}


# ==============================================================================
# 7. ТЕКСТЫ-ЗАГЛУШКИ
# ==============================================================================

TEXT_MEMORY = "Информацию необходимо смотреть в Msg_Other/pangea_***"

TEXT_SYSTEM_DISK = "Информацию необходимо смотреть в Msg_Other/scsi"

CATEGORY_SYSTEM_DISK = "System Disk Drive"

TEXT_NO_DESCRIPTION = "Описание отсутствует, требуется проверка в Spare Query"

TEXT_SFP_NO_BOM_TEMPLATE = "BOM в логе отсутствует (SFP, Vendor={vendor}, Model={model})"


# ==============================================================================
# 8. ФОРМАТ ИМЁН ВЫХОДНЫХ ФАЙЛОВ
# ==============================================================================

OUTPUT_NAME_TEMPLATE = "ЗИП_{name}_{timestamp}.xlsx"

TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


# ==============================================================================
# 9. ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ
# ==============================================================================

DEFAULT_VENDOR = "Huawei"

DEFAULT_QTY_ZIP = 1

DELTA_FORMULA_TEMPLATE = "=P{row}-Q{row}"