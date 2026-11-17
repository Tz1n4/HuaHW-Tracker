#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Workers.py — фоновые потоки для GUI.
"""

import os

from PyQt6.QtCore import QThread, pyqtSignal

from Core.Core_System_Info import parse_system_info


class QuickScanWorker(QThread):
    """Быстрое чтение только шапки логов (SUMMARY) для заполнения таблицы."""
    
    system_found_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, path, is_batch):
        super().__init__()
        self.path = path
        self.is_batch = is_batch

    def run(self):
        if not self.is_batch:
            files = [self.path]
        else:
            if not os.path.isdir(self.path):
                self.finished_signal.emit()
                return
            try:
                files = sorted([
                    os.path.join(self.path, f) 
                    for f in os.listdir(self.path) 
                    if f.lower().endswith(".txt") and os.path.isfile(os.path.join(self.path, f))
                ])
            except Exception:
                files = []

        for fpath in files:
            if not os.path.exists(fpath):
                continue
                
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    head = f.read(5000)
                
                sys_info = parse_system_info(head)
                
                if sys_info.get("name") == "N/A" and sys_info.get("model") == "N/A":
                    continue
                    
                row = {
                    "name":       sys_info.get("name", "N/A"),
                    "model":      sys_info.get("model", "N/A"),
                    "version":    sys_info.get("version", "N/A"),
                    "fw":         sys_info.get("fw", ""),
                    "serial":     sys_info.get("serial", "N/A"),
                    "components": "",
                    "log_path":   fpath,
                }
                self.system_found_signal.emit(row)
            except Exception:
                pass
                
        self.finished_signal.emit()


class SingleWorker(QThread):
    """Воркер для одиночного парсинга."""
    
    log_signal = pyqtSignal(str)
    system_signal = pyqtSignal(dict)
    component_progress_signal = pyqtSignal(str, int)
    finished_signal = pyqtSignal(bool, str, str)  # success, message, excel_path

    def __init__(self, file_path, include_synthetic=False, verbose_logging=False, customer="", project=""):
        super().__init__()
        self.file_path = file_path
        self.include_synthetic = include_synthetic
        self.verbose_logging = verbose_logging
        self.customer = customer
        self.project = project

    def run(self):
        try:
            from Core.Core_Base_Parser import HuaweiStorageParser
            from Core.Core_Export_Excel import ExcelExporter

            def progress_callback(text, percent):
                self.component_progress_signal.emit(text, percent)

            self.log_signal.emit(f"Reading file: {self.file_path}")
            parser = HuaweiStorageParser()
            sys_info, components = parser.parse_file(self.file_path, progress_callback=progress_callback)

            self.log_signal.emit(f"System: {sys_info.get('name')}")
            self.log_signal.emit(f"Model: {sys_info.get('model')}")
            self.log_signal.emit(f"Serial: {sys_info.get('serial')}")
            self.log_signal.emit(f"Version: {sys_info.get('version')}")
            self.log_signal.emit(f"Components: {len(components)}")

            if self.customer or self.project:
                self.log_signal.emit(f"Customer: {self.customer or '-'}")
                self.log_signal.emit(f"Project: {self.project or '-'}")

            self.log_signal.emit("Generating Excel...")
            exporter = ExcelExporter()
            output_dir = os.path.dirname(os.path.abspath(self.file_path))
            name_hint = os.path.splitext(os.path.basename(self.file_path))[0]

            result_path = exporter.export_single(
                sys_info=sys_info,
                components=components,
                output_dir=output_dir,
                name_hint=name_hint,
                include_synthetic=self.include_synthetic,
                customer=self.customer,
                project=self.project,
            )

            self.log_signal.emit(f"Excel created: {result_path}")
            
            row = {
                "name": sys_info.get("name", "N/A"),
                "model": sys_info.get("model", "N/A"),
                "version": sys_info.get("version", "N/A"),
                "fw": sys_info.get("fw", ""),
                "serial": sys_info.get("serial", "N/A"),
                "components": str(len(components)),
                "log_path": self.file_path,
            }
            self.system_signal.emit(row)
            self.system_signal.emit({"_update_excel_path": result_path})

            self.finished_signal.emit(True, f"Completed: {sys_info.get('name')}", result_path)
        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
            self.finished_signal.emit(False, str(e), "")


class BatchWorker(QThread):
    """Воркер для пакетного парсинга папки."""
    
    log_signal = pyqtSignal(str)
    system_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self, folder_path, include_synthetic=False, verbose_logging=False, customer="", project=""):
        super().__init__()
        self.folder_path = folder_path
        self.include_synthetic = include_synthetic
        self.verbose_logging = verbose_logging
        self.customer = customer
        self.project = project
        self._is_stopped = False

    def request_stop(self):
        self._is_stopped = True

    def run(self):
        try:
            from Core.Core_Base_Parser import HuaweiStorageParser
            from Core.Core_Export_Excel import ExcelExporter

            if not os.path.isdir(self.folder_path):
                self.finished_signal.emit(False, f"Not a folder: {self.folder_path}", "")
                return

            txt_files = sorted([
                f for f in os.listdir(self.folder_path)
                if f.lower().endswith(".txt") and os.path.isfile(os.path.join(self.folder_path, f))
            ])

            if not txt_files:
                self.finished_signal.emit(False, f"No .txt files in {self.folder_path}", "")
                return

            total = len(txt_files)
            self.log_signal.emit(f"Found {total} .txt file(s) in folder")

            parser = HuaweiStorageParser()
            systems_data = []
            success_count = 0
            error_count = 0

            for idx, fname in enumerate(txt_files, start=1):
                if self._is_stopped:
                    self.log_signal.emit("Stop requested. Finishing...")
                    break

                self.progress_signal.emit(idx, total, fname)
                self.log_signal.emit(f">>> Processing [{idx}/{total}]: {fname}")
                full_path = os.path.join(self.folder_path, fname)

                try:
                    sys_info, components = parser.parse_file(full_path)
                    systems_data.append((sys_info, components))
                    
                    self.log_signal.emit(f"    OK: {sys_info['name']} ({len(components)} components)")
                    success_count += 1
                    
                    row = {
                        "name": sys_info.get("name", "N/A"),
                        "model": sys_info.get("model", "N/A"),
                        "version": sys_info.get("version", "N/A"),
                        "fw": sys_info.get("fw", ""),
                        "serial": sys_info.get("serial", "N/A"),
                        "components": str(len(components)),
                        "log_path": full_path,
                    }
                    self.system_signal.emit(row)
                    
                except Exception as e:
                    error_count += 1
                    self.log_signal.emit(f"    SKIP: {e}")
                    self.system_signal.emit({
                        "name": fname,
                        "model": "ERROR",
                        "version": "",
                        "fw": "",
                        "serial": "",
                        "components": "0",
                        "log_path": full_path,
                        "_error": True,
                    })

            if self._is_stopped:
                self.finished_signal.emit(True, "Stopped by user", "")
                return

            if not systems_data:
                self.finished_signal.emit(False, f"No logs were parsed successfully ({error_count} errors).", "")
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

            self.system_signal.emit({"_update_excel_path_all": result_path})

            summary = f"Parsed: {success_count}/{total}"
            if error_count:
                summary += f", errors: {error_count}"
            
            self.log_signal.emit(summary)
            self.log_signal.emit(f"Excel created: {result_path}")

            self.finished_signal.emit(True, summary, result_path)
        except Exception as e:
            self.log_signal.emit(f"Critical error: {e}")
            self.finished_signal.emit(False, str(e), "")