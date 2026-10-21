#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Main.py — запуск GUI-приложения.

Функция gui_main() создаёт QApplication, загружает язык из Settings.ini,
показывает главное окно и запускает цикл событий.

ВАЖНО: файл сам добавляет свою папку в sys.path — обходит проблему
embedded Python, который не всегда делает это автоматически.
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

from Gui_App import HuaweiParserGUI
from Utils_Locale import set_language, DEFAULT_LANGUAGE

_SETTINGS_PATH = os.path.join(_SCRIPT_DIR, "Settings.ini")


def gui_main():
    """Запускает GUI. Возвращает код выхода QApplication."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from PyQt6.QtCore import QSettings
    from Utils_Locale import set_language, DEFAULT_LANGUAGE

    lang = DEFAULT_LANGUAGE
    try:
        s = QSettings(_SETTINGS_PATH, QSettings.Format.IniFormat)
        lang = s.value("General/language", DEFAULT_LANGUAGE, type=str)
        s.sync()
        del s                      # ← ВАЖНО: уничтожаем ДО создания окна
    except Exception:
        pass

    set_language(lang)

    window = HuaweiParserGUI()
    window.show()

    app.aboutToQuit.connect(window.save_settings_on_quit)
    return app.exec()
    
if __name__ == "__main__":
    sys.exit(gui_main())