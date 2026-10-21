#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core_Base_Parser.py — базовый парсер (диспетчер).

Класс HuaweiStorageParser:
- читает файл лога,
- определяет версию системы (через Core_System_Info),
- выбирает парсер (V6 / V5 / V3) по версии,
- запускает разбор и возвращает (sys_info, components).

Точка входа: parse_file(file_path, progress_callback=None).

progress_callback(step_text: str, percent: int) — опциональный.
Вызывается на каждом этапе парсинга для обновления прогресс-бара в GUI.
"""

import os

from Core.Core_System_Info import parse_system_info
from Parsers.Parser_V3 import V3Parser
from Parsers.Parser_V5 import V5Parser
from Parsers.Parser_V6 import V6Parser


# ==============================================================================
# Реестр парсеров
# ==============================================================================

PARSERS = {
    "V6": V6Parser,
    "V5": V5Parser,
    "V3": V3Parser,
}


# ==============================================================================
# Основной класс
# ==============================================================================

class HuaweiStorageParser:
    """Диспетчер парсеров Huawei Storage."""

    def __init__(self):
        self.version = "Unknown"
        self.sys_info = {}

    # --------------------------------------------------------------------------
    # Публичный API
    # --------------------------------------------------------------------------

    def parse_file(self, file_path, progress_callback=None):
        """
        Читает файл лога, определяет версию и разбирает компоненты.

        :param file_path: путь к .txt логу
        :param progress_callback: опциональный callback (step_text, percent)
        :return: (sys_info, components)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Log file not found: {file_path}")

        if progress_callback:
            progress_callback("Reading file...", 5)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        return self.parse_content(content, progress_callback=progress_callback)

    def parse_content(self, content, progress_callback=None):
        """
        Разбирает уже прочитанное содержимое лога.

        :param content: str — полный текст лога
        :param progress_callback: опциональный callback (step_text, percent)
        :return: (sys_info, components)
        """
        if progress_callback:
            progress_callback("Parsing system info...", 10)

        self.sys_info = parse_system_info(content)
        self.version = self.sys_info.get("version", "Unknown")

        if self.version not in PARSERS:
            raise ValueError(
                f"Unsupported system version: '{self.version}'. "
                f"Supported: {list(PARSERS.keys())}"
            )

        parser_cls = PARSERS[self.version]

        parser = parser_cls(content, self.sys_info)
        components = parser.parse_all(progress_callback=progress_callback)

        return self.sys_info, components