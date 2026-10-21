#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Workers.py — QThread-воркеры для GUI.

Содержит два класса:
- SingleWorker: обработка одного .txt лога.
- BatchWorker:  обработка папки с логами, объединение в один Excel.

Работают напрямую (без subprocess) — парсер и экспортёр в одном процессе.

Сигналы:
- log_signal(str)                 — сообщения в консоль
- system_signal(dict)             — данные СХД для таблицы Systems
- progress_signal(int, int, str)  — только BatchWorker: (текущий, всего, имя файла)
- finished_signal(bool, str, str) — (успех, сообщение, путь к Excel)
"""

import os
import traceback
from collections import Counter

from PyQt6.QtCore import QThread, pyqtSignal

from Core.Core_Base_Parser import HuaweiStorageParser
from Core.Core_Export_Excel import ExcelExporter


# ==============================================================================
# ОБЩИЕ ХЕЛПЕРЫ (используются SingleWorker и BatchWorker)
# ==============================================================================

def _log_sys_info(emit, sys_info, components):
    """Пишет стандартный блок System / Model / Serial / Version / Components."""
    emit(f"System:  {sys_info['name']}")
    emit(f"Model:   {sys_info['model']}")
    emit(f"Serial:  {sys_info['serial']}")
    emit(f"Version: {sys_info['version']}")
    emit(f"Components: {len(components)}")


def _log_customer_project(emit, customer, project):
    """Пишет строки Customer / Project, если хотя бы одно задано."""
    if customer or project:
        emit(f"Customer: {customer or '-'}")
        emit(f"Project:  {project or '-'}")


def _count_unique_bom(components):
    """Считает уникальные пары (type, bom), отбрасывая пустые/N/A."""
    return len({
        (c.get("type", ""), c.get("bom", ""))
        for c in components
        if c.get("bom") and c.get("bom") != "N/A"
    })


def _type_breakdown(components):
    """Возвращает Counter по типам компонентов."""
    return Counter(c.get("type", "?") for c in components)


def _log_verbose_single(emit, components, include_synthetic, indent="    "):
    """Verbose-разбивка для одного лога (используется в Single и в Batch)."""
    for t, n in sorted(_type_breakdown(components).items()):
        emit(f"{indent}{t:20} : {n}")

    n_unique = _count_unique_bom(components)
    synthetic_n = 2 if include_synthetic else 0
    emit(f"{indent}Excel rows: 1 root + {n_unique} components "
         f"+ {synthetic_n} synthetic")


def _log_batch_summary(emit, systems_data, success_count, error_count,
                       total, elapsed, include_synthetic):
    """Итоговая сводка для batch-режима."""
    total_components = 0
    total_unique_bom = 0
    total_breakdown = Counter()

    for _sys_info, comps in systems_data:
        total_components += len(comps)
        total_unique_bom += _count_unique_bom(comps)
        total_breakdown.update(_type_breakdown(comps))

    emit("")
    emit("    Batch summary:")
    emit(f"      Total files     : {total}")
    emit(f"      Parsed          : {success_count}")
    emit(f"      Errors          : {error_count}")
    emit(f"      Components      : {total_components}")
    emit(f"      Unique BOMs     : {total_unique_bom}")
    emit(f"      Elapsed time    : {elapsed:.1f} s")

    if total_breakdown:
        emit("")
        emit("    Total breakdown by type:")
        for t, n in sorted(total_breakdown.items()):
            emit(f"      {t:20} : {n}")


def make_system_row(sys_info, components, log_path):
    """Собирает словарь для одной строки таблицы Systems."""
    return {
        "name":       sys_info.get("name", "N/A"),
        "model":      sys_info.get("model", "N/A"),
        "version":    sys_info.get("version", "N/A"),
        "fw":         sys_info.get("fw", ""),
        "serial":     sys_info.get("serial", "N/A"),
        "location":   sys_info.get("location", "N/A"),
        "components": len(components),
        "log_path":   log_path,
    }


def make_error_row(source_name, error_message):
    """Собирает словарь-ошибку для таблицы Systems."""
    name = os.path.splitext(source_name)[0]
    return {
        "name":       name,
        "model":      "",
        "version":    "",
        "fw":         "",
        "serial":     "",
        "location":   "",
        "components": 0,
        "_error":     error_message,
    }


# ==============================================================================
# SINGLE WORKER
# ==============================================================================

class SingleWorker(QThread):
    """Обрабатывает один .txt лог и сохраняет один Excel."""

    log_signal = pyqtSignal(str)
    system_signal = pyqtSignal(dict)
    component_progress_signal = pyqtSignal(str, int)
    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self, log_path, include_synthetic=True, verbose_logging=False,
                 customer="", project=""):
        super().__init__()
        self.log_path = log_path
        self.include_synthetic = include_synthetic
        self.verbose_logging = verbose_logging
        self.customer = customer
        self.project = project

    def run(self):
        try:
            self.log_signal.emit(f"Reading file: {self.log_path}")

            parser = HuaweiStorageParser()

            def on_progress(text, percent):
                self.component_progress_signal.emit(text, percent)

            sys_info, components = parser.parse_file(
                self.log_path,
                progress_callback=on_progress,
            )

            _log_sys_info(self.log_signal.emit, sys_info, components)
            _log_customer_project(
                self.log_signal.emit, self.customer, self.project
            )

            if self.verbose_logging:
                self.log_signal.emit("    Component breakdown:")
                _log_verbose_single(
                    self.log_signal.emit,
                    components,
                    self.include_synthetic,
                )

            self.system_signal.emit(
                make_system_row(sys_info, components, self.log_path)
            )

            self.component_progress_signal.emit("Generating Excel...", 98)

            exporter = ExcelExporter()
            output_dir = os.path.dirname(os.path.abspath(self.log_path))
            name_hint = os.path.splitext(os.path.basename(self.log_path))[0]

            result_path = exporter.export_single(
                sys_info=sys_info,
                components=components,
                output_dir=output_dir,
                name_hint=name_hint,
                include_synthetic=self.include_synthetic,
                customer=self.customer,
                project=self.project,
            )

            self.component_progress_signal.emit("Done", 100)

            self.system_signal.emit({
                "_update_excel_path": result_path,
            })

            self.log_signal.emit(f"Excel created: {result_path}")
            self.finished_signal.emit(
                True, "Parsing completed successfully!", result_path
            )

        except FileNotFoundError as e:
            msg = f"File not found: {e}"
            self.log_signal.emit(msg)
            self.system_signal.emit(
                make_error_row(os.path.basename(self.log_path), msg)
            )
            self.finished_signal.emit(False, msg, "")

        except ValueError as e:
            msg = f"Parsing error: {e}"
            self.log_signal.emit(msg)
            self.system_signal.emit(
                make_error_row(os.path.basename(self.log_path), msg)
            )
            self.finished_signal.emit(False, msg, "")

        except Exception as e:
            tb = traceback.format_exc()
            self.log_signal.emit(tb)
            msg = f"Critical error: {e}"
            self.system_signal.emit(
                make_error_row(os.path.basename(self.log_path), msg)
            )
            self.finished_signal.emit(False, msg, "")


# ==============================================================================
# BATCH WORKER
# ==============================================================================

class BatchWorker(QThread):
    """Обрабатывает все .txt в папке и объединяет результат в один Excel."""

    log_signal = pyqtSignal(str)
    system_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self, folder_path, include_synthetic=True, verbose_logging=False,
                 customer="", project=""):
        super().__init__()
        self.folder_path = folder_path
        self.include_synthetic = include_synthetic
        self.verbose_logging = verbose_logging
        self.customer = customer
        self.project = project
        self._stop_requested = False

    def request_stop(self):
        """Запрос мягкой остановки — текущий файл дописывается, следующий не начинается."""
        self._stop_requested = True

    def run(self):
        import time
        start_time = time.time()

        try:
            txt_files = sorted([
                f for f in os.listdir(self.folder_path)
                if f.lower().endswith(".txt")
                and os.path.isfile(os.path.join(self.folder_path, f))
            ])

            if not txt_files:
                self.finished_signal.emit(
                    False, "No .txt files found in selected folder!", ""
                )
                return

            total = len(txt_files)
            self.log_signal.emit(f"Found {total} .txt file(s) in folder")

            _log_customer_project(
                self.log_signal.emit, self.customer, self.project
            )

            self.log_signal.emit("")

            parser = HuaweiStorageParser()
            systems_data = []
            success_count = 0
            error_count = 0

            for idx, fname in enumerate(txt_files, start=1):
                if self._stop_requested:
                    self.log_signal.emit("")
                    self.log_signal.emit(
                        f"⏹ STOP requested — processed {idx - 1}/{total} files."
                    )
                    break

                self.progress_signal.emit(idx, total, fname)
                self.log_signal.emit(f">>> Processing [{idx}/{total}]: {fname}")

                full_path = os.path.join(self.folder_path, fname)

                try:
                    sys_info, components = parser.parse_file(full_path)
                    systems_data.append((sys_info, components))
                    self.log_signal.emit(
                        f"    OK: {sys_info['name']} ({len(components)} components)"
                    )
                    success_count += 1

                    if self.verbose_logging:
                        self.log_signal.emit("        Component breakdown:")
                        _log_verbose_single(
                            self.log_signal.emit,
                            components,
                            self.include_synthetic,
                            indent="          ",
                        )

                    self.system_signal.emit(
                        make_system_row(sys_info, components, full_path)
                    )

                except Exception as e:
                    error_count += 1
                    self.log_signal.emit(f"    SKIP: {e}")
                    self.system_signal.emit(
                        make_error_row(fname, str(e))
                    )

                self.log_signal.emit("")

            if not systems_data:
                self.finished_signal.emit(
                    False,
                    f"No logs were parsed successfully ({error_count} errors).",
                    "",
                )
                return

            self.log_signal.emit("Generating combined Excel...")

            exporter = ExcelExporter()
            folder_name = os.path.basename(os.path.normpath(self.folder_path))

            result_path = exporter.export_batch(
                systems_data=systems_data,
                output_dir=self.folder_path,
                folder_name=folder_name,
                include_synthetic=self.include_synthetic,
                customer=self.customer,
                project=self.project,
            )

            if self.verbose_logging:
                elapsed = time.time() - start_time
                _log_batch_summary(
                    self.log_signal.emit,
                    systems_data,
                    success_count,
                    error_count,
                    total,
                    elapsed,
                    self.include_synthetic,
                )

            self.log_signal.emit(f"Excel created: {result_path}")
            self.log_signal.emit("")

            self.system_signal.emit({
                "_update_excel_path_all": result_path,
            })

            stop_note = " (stopped by user)" if self._stop_requested else ""
            msg = (
                f"Batch completed! "
                f"Parsed: {success_count}/{total}"
                + (f", errors: {error_count}" if error_count else "")
                + stop_note
            )
            self.finished_signal.emit(True, msg, result_path)

        except Exception as e:
            tb = traceback.format_exc()
            self.log_signal.emit(tb)
            self.finished_signal.emit(False, f"Critical batch error: {e}", "")