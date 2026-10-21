#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main.py — точка входа парсера Huawei Storage.

Режимы работы:
1. Без аргументов:
    python Main.py
    → запускается GUI (PyQt6).

2. Один файл (single-режим):
    python Main.py log.txt
    → парсит один лог, создаёт один Excel рядом с логом.

3. Папка (batch-режим):
    python Main.py C:\\Logs
    → парсит все .txt в папке, создаёт один общий Excel со всеми СХД.

4. Принудительный batch:
    python Main.py --batch C:\\Logs
    → то же, что и п.3 (на случай, если папка без .txt в имени).

5. Опции Заказчик / Проект (колонки B и C в Excel):
    python Main.py log.txt --customer "ПАО Ростелеком" --project "ЦОД-МСК-2026"
    python Main.py C:\\Logs --customer "ПАО Ростелеком" --project "ЦОД-МСК-2026"

6. Специальные команды:
    python Main.py --help, -h      → справка
    python Main.py --readme        → открыть README.txt
    python Main.py --selftest      → Self-test в консоли
    python Main.py --changelog     → открыть CHANGELOG.txt

ВАЖНО: файл сам добавляет свою папку в sys.path — обходит проблему
embedded Python, который не всегда делает это автоматически.
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from Utils_System import open_in_system
from Utils_Locale import tr, trf, set_language, DEFAULT_LANGUAGE


# ==============================================================================
# ЗАГРУЗКА ЯЗЫКА
# ==============================================================================

_SETTINGS_PATH = os.path.join(_SCRIPT_DIR, "Settings.ini")


def _load_language():
    """Читает язык из Settings.ini и применяет. Тихо игнорирует ошибки."""
    lang = DEFAULT_LANGUAGE
    try:
        from PyQt6.QtCore import QSettings
        s = QSettings(_SETTINGS_PATH, QSettings.Format.IniFormat)
        lang = s.value("General/language", DEFAULT_LANGUAGE, type=str)
    except Exception:
        pass
    set_language(lang)


# ==============================================================================
# КОНСОЛЬНЫЙ РЕЖИМ — SINGLE
# ==============================================================================

def run_single(log_path, customer="", project=""):
    """Парсит один лог-файл и сохраняет один Excel."""
    from Core_Base_Parser import HuaweiStorageParser
    from Export_Excel import ExcelExporter

    print(trf("cli_reading_file", path=log_path))

    parser = HuaweiStorageParser()
    sys_info, components = parser.parse_file(log_path)

    print(trf("cli_system",     name=sys_info['name']))
    print(trf("cli_model",      model=sys_info['model']))
    print(trf("cli_serial",     serial=sys_info['serial']))
    print(trf("cli_version",    version=sys_info['version']))
    print(trf("cli_components", n=len(components)))

    if customer or project:
        print(trf("cli_customer", customer=customer or "-"))
        print(trf("cli_project",  project=project or "-"))

    print(tr("cli_generating"))

    exporter = ExcelExporter()
    output_dir = os.path.dirname(os.path.abspath(log_path))
    name_hint = os.path.splitext(os.path.basename(log_path))[0]

    result_path = exporter.export_single(
        sys_info=sys_info,
        components=components,
        output_dir=output_dir,
        name_hint=name_hint,
        customer=customer,
        project=project,
    )

    print(trf("cli_excel_created", path=result_path))
    return 0


# ==============================================================================
# КОНСОЛЬНЫЙ РЕЖИМ — BATCH
# ==============================================================================

def run_batch(folder_path, customer="", project=""):
    """Парсит все .txt в папке и сохраняет один общий Excel."""
    from Core_Base_Parser import HuaweiStorageParser
    from Export_Excel import ExcelExporter

    if not os.path.isdir(folder_path):
        print(trf("cli_err_not_folder", path=folder_path))
        return 1

    txt_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".txt")
        and os.path.isfile(os.path.join(folder_path, f))
    ])

    if not txt_files:
        print(trf("cli_err_no_txt", path=folder_path))
        return 1

    total = len(txt_files)
    print(trf("cli_found_files", n=total))

    if customer or project:
        print(trf("cli_customer", customer=customer or "-"))
        print(trf("cli_project",  project=project or "-"))

    print()

    parser = HuaweiStorageParser()
    systems_data = []
    success_count = 0
    error_count = 0

    for idx, fname in enumerate(txt_files, start=1):
        print(trf("cli_processing", idx=idx, total=total, name=fname))
        full_path = os.path.join(folder_path, fname)

        try:
            sys_info, components = parser.parse_file(full_path)
            systems_data.append((sys_info, components))
            print(trf("cli_ok", name=sys_info['name'], n=len(components)))
            success_count += 1
        except Exception as e:
            error_count += 1
            print(trf("cli_skip", e=e))

    print()

    if not systems_data:
        print(trf("cli_no_success", n=error_count))
        return 1

    print(tr("cli_generating_batch"))

    exporter = ExcelExporter()
    folder_name = os.path.basename(os.path.normpath(folder_path))

    result_path = exporter.export_batch(
        systems_data=systems_data,
        output_dir=folder_path,
        folder_name=folder_name,
        customer=customer,
        project=project,
    )

    print()
    summary = trf("cli_parsed_summary", ok=success_count, total=total)
    if error_count:
        summary += trf("cli_errors_suffix", n=error_count)
    print(summary)
    print(trf("cli_excel_created", path=result_path))
    return 0


# ==============================================================================
# GUI-РЕЖИМ
# ==============================================================================

def run_gui():
    """Запускает GUI."""
    from Gui_Main import gui_main
    return gui_main()


# ==============================================================================
# СПЕЦИАЛЬНЫЕ КОМАНДЫ
# ==============================================================================

def open_readme():
    """Открывает README.txt в системном просмотрщике."""
    readme_path = os.path.join(_SCRIPT_DIR, "README.txt")

    if not os.path.exists(readme_path):
        print(trf("cli_err_open", what="README.txt", e=readme_path))
        return 1

    if open_in_system(readme_path):
        print(trf("cli_opened", path=readme_path))
        return 0

    print(trf("cli_err_open", what="README.txt", e=readme_path))
    return 1


def open_changelog():
    """Открывает CHANGELOG.txt в системном просмотрщике."""
    path = os.path.join(_SCRIPT_DIR, "CHANGELOG.txt")

    if not os.path.exists(path):
        print(trf("cli_err_open", what="CHANGELOG.txt", e=path))
        return 1

    if open_in_system(path):
        print(trf("cli_opened", path=path))
        return 0

    print(trf("cli_err_open", what="CHANGELOG.txt", e=path))
    return 1


def run_selftest_cli():
    """Runs self-test in console mode."""
    try:
        from Utils_SelfTest import run_checks
    except ImportError:
        print(tr("cli_selftest_module_missing"))
        return 1

    print("=" * 60)
    print(tr("cli_selftest_header"))
    print("=" * 60)

    results = run_checks()
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count

    for r in results:
        mark = "✓" if r["ok"] else "✗"
        line = f"  [{mark}] {r['label']}"
        if r.get("extra"):
            line += f" — {r['extra']}"
        print(line)

    print("=" * 60)
    print(trf("cli_selftest_result", ok=ok_count, fail=fail_count))
    print("=" * 60)

    return 0 if fail_count == 0 else 1


def print_usage():
    """Prints usage help."""
    print()
    print(tr("cli_usage_title"))
    print(tr("cli_usage_gui"))
    print(tr("cli_usage_single"))
    print(tr("cli_usage_batch"))
    print(tr("cli_usage_batch_force"))
    print()
    print(tr("cli_usage_options_title"))
    print(tr("cli_usage_customer"))
    print(tr("cli_usage_project"))
    print()
    print(tr("cli_special_title"))
    print(tr("cli_help"))
    print(tr("cli_readme"))
    print(tr("cli_selftest"))
    print(tr("cli_changelog"))


# ==============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ==============================================================================

def main():
    """Entry point. Parses arguments and selects mode."""
    _load_language()

    args = sys.argv[1:]

    if not args:
        return run_gui()

    if "--help" in args or "-h" in args:
        print_usage()
        return 0

    if "--readme" in args:
        return open_readme()

    if "--selftest" in args:
        return run_selftest_cli()

    if "--changelog" in args:
        return open_changelog()

    force_batch = False
    path_arg = None
    customer = ""
    project = ""

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--batch":
            force_batch = True

        elif arg == "--customer":
            if i + 1 >= len(args):
                print(trf("cli_err_missing_value", flag="--customer"))
                return 1
            customer = args[i + 1]
            i += 1

        elif arg == "--project":
            if i + 1 >= len(args):
                print(trf("cli_err_missing_value", flag="--project"))
                return 1
            project = args[i + 1]
            i += 1

        elif path_arg is None:
            path_arg = arg

        else:
            print(trf("cli_warn_unexpected", arg=arg))

        i += 1

    if path_arg is None:
        print(tr("cli_err_no_path"))
        print_usage()
        return 1

    if not os.path.exists(path_arg):
        print(trf("cli_err_path_not_found", path=path_arg))
        return 1

    if force_batch:
        if not os.path.isdir(path_arg):
            print(trf("cli_err_batch_needs_dir", path=path_arg))
            return 1
        return run_batch(path_arg, customer=customer, project=project)

    if os.path.isdir(path_arg):
        return run_batch(path_arg, customer=customer, project=project)

    if not path_arg.lower().endswith(".txt"):
        print(trf("cli_warn_not_txt", path=path_arg))
        print("Continuing anyway...")

    return run_single(path_arg, customer=customer, project=project)


# ==============================================================================
# ЗАПУСК
# ==============================================================================

if __name__ == "__main__":
    sys.exit(main())