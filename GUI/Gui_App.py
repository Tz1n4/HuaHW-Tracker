#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_App.py — главное окно GUI (PyQt6).
"""

import os
import csv
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QProgressBar, QStatusBar, QTabWidget, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QMenu, QComboBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QGuiApplication, QColor, QAction, QKeySequence

from GUI.Gui_Workers import SingleWorker, BatchWorker, QuickScanWorker
from GUI.Gui_Settings import SettingsDialog
from GUI.Gui_Dialogs.Gui_Dialog_Detailed_Analysis import DetailedAnalysisDialog
from GUI.Gui_Dialogs.Gui_Dialog_Customer import CustomerDialog
from GUI.Gui_SelfTest import SelfTestDialog
from GUI.Gui_Styles import (
    STYLE_BTN_ACTIVE, STYLE_BTN_INACTIVE, STYLE_BTN_DARK, STYLE_BTN_DANGER
)
from Utils.Utils_Settings import (
    read_mode, write_mode, read_components, write_components
)
from Utils.Utils_System import open_in_system, open_url, reveal_path
from Utils.Utils_Constants import (
    PARSER_NAME, PARSER_VERSION, SUPPORTED_VERSIONS_DESCRIPTION, USEFUL_LINKS
)
from Utils.Utils_Locale import tr, trf


class HuaHWTrackerGUI(QMainWindow):

    def __init__(self):
        super().__init__()

        self.settings = QSettings("Settings.ini", QSettings.Format.IniFormat)
        self.settings.setFallbacksEnabled(False)

        self.worker = None
        self.scan_worker = None
        self.last_excel_path = ""
        
        # Режимы работы: 0 = Single, 1 = Batch, 2-4 = WIP
        self.current_mode_idx = 1 
        
        self.detailed_components = []
        self._initializing = True

        self.init_ui()
        self.setAcceptDrops(True)
        self._load_settings()

        self._initializing = False

    # --------------------------------------------------------------------------
    # QSETTINGS — ЗАГРУЗКА
    # --------------------------------------------------------------------------

    def _load_settings(self):
        self.detailed_components = read_components()

        start_mode = self.settings.value("General/start_mode", "last", type=str)
        file_mode = read_mode()

        # Восстанавливаем индекс
        if start_mode == "single":
            idx = 0
        elif start_mode == "batch":
            idx = 1
        else:
            idx = 0 if file_mode == "single" else 1
            
        self.mode_combo.setCurrentIndex(idx)
        self._on_mode_changed(idx)

        last_file = self.settings.value("General/last_file", "", type=str)
        last_folder = self.settings.value("General/last_folder", "", type=str)

        if self.is_batch_mode():
            if last_folder:
                self.path_edit.setText(last_folder)
                self._start_quick_scan(last_folder)
        else:
            if last_file:
                self.path_edit.setText(last_file)
                self._start_quick_scan(last_file)

        active_tab = self.settings.value("General/active_tab", 0, type=int)
        if 0 <= active_tab < self.tabs.count():
            self.tabs.setCurrentIndex(active_tab)

        self._restore_geometry()

    def _restore_geometry(self):
        width = self.settings.value("Window/width", 1000, type=int)
        height = self.settings.value("Window/height", 750, type=int)
        x = self.settings.value("Window/x", -1, type=int)
        y = self.settings.value("Window/y", -1, type=int)

        width = max(width, 800)
        height = max(height, 600)

        if x >= 0 and y >= 0:
            screen = QGuiApplication.primaryScreen()
            if screen is not None:
                screen_geo = screen.availableGeometry()
                if x + width > screen_geo.right() or x < screen_geo.left() or \
                   y + height > screen_geo.bottom() or y < screen_geo.top():
                    x = (screen_geo.width() - width) // 2
                    y = (screen_geo.height() - height) // 2

            self.resize(width, height)
            self.move(x, y)
        else:
            self.resize(width, height)

    # --------------------------------------------------------------------------
    # QSETTINGS — СОХРАНЕНИЕ
    # --------------------------------------------------------------------------

    def _save_settings(self):
        path = self.path_edit.text().strip()
        if path:
            if self.is_batch_mode():
                self.settings.setValue("General/last_folder", path)
            else:
                self.settings.setValue("General/last_file", path)

        write_components(self.detailed_components)
        self.settings.setValue("General/active_tab", self.tabs.currentIndex())

        geo = self.geometry()
        self.settings.setValue("Window/width", geo.width())
        self.settings.setValue("Window/height", geo.height())
        self.settings.setValue("Window/x", geo.x())
        self.settings.setValue("Window/y", geo.y())

        self.settings.sync()

    def _save_on_change(self):
        path = self.path_edit.text().strip()
        if path:
            if self.is_batch_mode():
                self.settings.setValue("General/last_folder", path)
            else:
                self.settings.setValue("General/last_file", path)

        write_components(self.detailed_components)
        self.settings.setValue("General/active_tab", self.tabs.currentIndex())
        self.settings.sync()

    def save_settings_on_quit(self):
        try:
            self._save_settings()
            if self.is_batch_mode():
                write_mode(True)
            else:
                write_mode(False)
        except Exception as e:
            print(f"Failed to save settings on quit: {e}")

    def closeEvent(self, event):
        try:
            self._save_settings()
            if self.is_batch_mode():
                write_mode(True)
            else:
                write_mode(False)
        except Exception as e:
            print(f"Failed to save settings: {e}")
        event.accept()

    # --------------------------------------------------------------------------
    # ЛОГИКА РЕЖИМОВ
    # --------------------------------------------------------------------------

    def is_batch_mode(self):
        return self.current_mode_idx == 1

    def is_wip_mode(self):
        return self.current_mode_idx >= 2

    def _on_mode_changed(self, idx):
        self.current_mode_idx = idx
        
        if self.is_wip_mode():
            self.mode_label.setText(trf("mode_current", mode=f"<b>{tr('mode_wip')}</b>"))
            self.mode_label.setStyleSheet("color: #F44336;")
            self.action_btn.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.path_edit.clear()
        else:
            self.action_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            
            if idx == 0:
                self.mode_label.setText(trf("mode_current", mode=f"<b>{tr('combo_mode_single')}</b>"))
                self.path_label.setText(tr("label_log_file"))
                self.path_edit.setPlaceholderText(tr("placeholder_file"))
                self.browse_btn.setText(tr("browse"))
            else:
                self.mode_label.setText(trf("mode_current", mode=f"<b>{tr('combo_mode_batch')}</b>"))
                self.path_label.setText(tr("label_log_folder"))
                self.path_edit.setPlaceholderText(tr("placeholder_folder"))
                self.browse_btn.setText(tr("btn_browse_folder"))

        self.mode_label.setStyleSheet("color: #aaa;")
        self.path_edit.clear()
        self.last_excel_path = ""
        self.open_folder_btn.setEnabled(False)

        if not self._initializing:
            self._save_on_change()

    # --------------------------------------------------------------------------
    # БЫСТРОЕ СКАНИРОВАНИЕ
    # --------------------------------------------------------------------------

    def _start_quick_scan(self, path):
        if not path or not os.path.exists(path):
            return
            
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.terminate()
            self.scan_worker.wait()

        self.systems_table.setRowCount(0)

        self.scan_worker = QuickScanWorker(path, self.is_batch_mode())
        self.scan_worker.system_found_signal.connect(self.add_system_row)
        self.scan_worker.finished_signal.connect(
            lambda: self.status_bar.showMessage(tr("ready"), 3000)
        )
        self.scan_worker.start()
        self.status_bar.showMessage(tr("processing"))

    # --------------------------------------------------------------------------
    # DRAG & DROP
    # --------------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().hasUrls() and event.mimeData().urls()
        if not urls:
            return

        path = urls[0].toLocalFile()
        if not path:
            return

        if os.path.isdir(path):
            self.mode_combo.setCurrentIndex(1)
            self.path_edit.setText(path)
            self.append_to_console(f"[Drop] Folder dropped: {path}")
            self._save_on_change()
            self.tabs.setCurrentIndex(1)
            self._start_quick_scan(path)

        elif os.path.isfile(path):
            if path.lower().endswith(".txt"):
                self.mode_combo.setCurrentIndex(0)
                self.path_edit.setText(path)
                self.append_to_console(f"[Drop] File dropped: {path}")
                self._save_on_change()
                self.tabs.setCurrentIndex(1)
                self._start_quick_scan(path)
            else:
                QMessageBox.warning(
                    self, tr("warning"), tr("err_drop_unsupported")
                )

        event.acceptProposedAction()

    # --------------------------------------------------------------------------
    # ИНТЕРФЕЙС
    # --------------------------------------------------------------------------

    def init_ui(self):
        self.setWindowTitle(
            trf("app_title", name=PARSER_NAME, version=PARSER_VERSION)
        )
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self._build_menu_bar()

        # --- БЛОК ВЫБОРА РЕЖИМА ---
        source_layout = QHBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.setFont(QFont("Arial", 10))
        self.mode_combo.addItems([
            tr("combo_mode_single"),
            tr("combo_mode_batch"),
            tr("combo_mode_archive"),
            tr("combo_mode_archive_folder"),
            tr("combo_mode_auto")
        ])
        
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d; color: #d4d4d4;
                border: 1px solid #555; border-radius: 5px;
                padding: 5px 10px; font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #888;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d; color: #d4d4d4;
                selection-background-color: #2196F3;
                border: 1px solid #555;
            }
        """)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        
        self.mode_label = QLabel(trf("mode_current", mode=f"<b>{tr('combo_mode_batch')}</b>"))
        self.mode_label.setFont(QFont("Arial", 10))
        self.mode_label.setStyleSheet("color: #aaa;")

        source_layout.addWidget(self.mode_combo, 1)
        source_layout.addSpacing(20)
        source_layout.addWidget(self.mode_label, 2)
        
        main_layout.addLayout(source_layout)

        # --- ПОЛЕ ВВОДА ПУТИ ---
        input_layout = QHBoxLayout()
        self.path_label = QLabel(tr("label_log_folder"))
        self.path_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(tr("placeholder_folder"))
        self.path_edit.setReadOnly(True)

        self.browse_btn = QPushButton(tr("btn_browse_folder"))
        self.browse_btn.clicked.connect(self.browse_input)

        input_layout.addWidget(self.path_label)
        input_layout.addWidget(self.path_edit, 1)
        input_layout.addWidget(self.browse_btn)
        main_layout.addLayout(input_layout)

        # --- КНОПКИ ЗАПУСКА ---
        btn_layout = QHBoxLayout()

        self.action_btn = QPushButton(tr("btn_run"))
        self.action_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.action_btn.setStyleSheet(STYLE_BTN_DARK)
        self.action_btn.setShortcut(QKeySequence("F9"))
        self.action_btn.clicked.connect(self.run_parser)

        self.open_folder_btn = QPushButton(tr("btn_open_result"))
        self.open_folder_btn.setFont(QFont("Arial", 10))
        self.open_folder_btn.setStyleSheet(STYLE_BTN_DARK)
        self.open_folder_btn.clicked.connect(self.open_result_folder)
        self.open_folder_btn.setEnabled(False)

        btn_layout.addWidget(self.action_btn, 1)
        btn_layout.addWidget(self.open_folder_btn, 1)
        main_layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.queue_label = QLabel("")
        self.queue_label.setFont(QFont("Arial", 9))
        self.queue_label.setStyleSheet("color: #aaa;")
        main_layout.addWidget(self.queue_label)

        # --- ВКЛАДКИ КОНСОЛИ И СИСТЕМ ---
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 10))
        self.tabs.currentChanged.connect(self._save_on_change)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.tabs.addTab(self.console, tr("tab_console"))

        self.systems_table = QTableWidget()
        self.systems_table.setColumnCount(5)
        self.systems_table.setHorizontalHeaderLabels([
            tr("col_sys_name"), tr("col_model"), tr("col_version"),
            tr("col_serial"), tr("col_components"),
        ])
        self.systems_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.systems_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.systems_table.setAlternatingRowColors(True)
        self.systems_table.setSortingEnabled(True)
        self.systems_table.verticalHeader().setVisible(False)
        self.systems_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.systems_table.customContextMenuRequested.connect(self._show_systems_context_menu)

        header = self.systems_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.systems_table.setColumnWidth(0, 220)
        self.systems_table.setColumnWidth(1, 180)
        self.systems_table.setColumnWidth(2, 150)
        self.systems_table.setColumnWidth(3, 200)

        self.tabs.addTab(self.systems_table, tr("tab_systems"))
        main_layout.addWidget(self.tabs, 1)

        # --- НИЖНИЕ КНОПКИ ---
        bottom_layout = QHBoxLayout()

        self.clear_btn = QPushButton(tr("btn_clear"))
        self.clear_btn.setFont(QFont("Arial", 10))
        self.clear_btn.setStyleSheet(STYLE_BTN_DARK)
        self.clear_btn.clicked.connect(self.clear_current_tab)

        self.export_btn = QPushButton(tr("btn_export"))
        self.export_btn.setFont(QFont("Arial", 10))
        self.export_btn.setStyleSheet(STYLE_BTN_DARK)
        self.export_btn.clicked.connect(self._show_export_menu)

        bottom_layout.addWidget(self.clear_btn, 1)
        bottom_layout.addWidget(self.export_btn, 1)
        bottom_layout.addStretch(3)

        main_layout.addLayout(bottom_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(tr("ready"))

    # --------------------------------------------------------------------------
    # ЗАПУСК
    # --------------------------------------------------------------------------

    def run_parser(self):
        if not self.validate_inputs():
            return

        self._save_on_change()

        self._save_on_change()

        customer = ""
        project = ""

        ask_customer = self.settings.value("General/ask_customer", True, type=bool)
        if ask_customer:
            dlg = CustomerDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                self.status_bar.showMessage(tr("ready"), 3000)
                return
            customer, project = dlg.values()

        self.tabs.setCurrentIndex(0)

        if self.is_batch_mode():
            self._set_action_state("running")
        else:
            self._set_action_state("single")
            
        self.open_folder_btn.setEnabled(False)
        self.last_excel_path = ""

        if self.settings.value("General/clear_console", True, type=bool):
            self.console.clear()

        if self.settings.value("General/clear_table", True, type=bool):
            self.systems_table.setRowCount(0)

        self.progress_bar.setVisible(True)
        self.queue_label.setText("")
        self.append_to_console("=" * 60)

        path = self.path_edit.text()
        include_synthetic = self.settings.value("General/include_synthetic", False, type=bool)
        verbose_logging = self.settings.value("General/verbose_logging", False, type=bool)

        if self.is_batch_mode():
            self.append_to_console(tr("console_start_batch"))
            self.append_to_console(trf("console_folder", path=path))
            self.append_to_console("=" * 60)
            self.progress_bar.setRange(0, 0)
            self.worker = BatchWorker(
                path, include_synthetic=include_synthetic,
                verbose_logging=verbose_logging, customer=customer, project=project
            )
            self.worker.log_signal.connect(self.append_to_console)
            self.worker.system_signal.connect(self.add_system_row)
            self.worker.progress_signal.connect(self.update_batch_progress)
            self.worker.finished_signal.connect(self.on_finished)
        else:
            self.append_to_console(tr("console_start_single"))
            self.append_to_console(trf("console_file", path=path))
            self.append_to_console("=" * 60)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.worker = SingleWorker(
                path, include_synthetic=include_synthetic,
                verbose_logging=verbose_logging, customer=customer, project=project
            )
            self.worker.log_signal.connect(self.append_to_console)
            self.worker.system_signal.connect(self.add_system_row)
            self.worker.component_progress_signal.connect(self.on_component_progress)
            self.worker.finished_signal.connect(self.on_finished)

        self.worker.start()
        self.status_bar.showMessage(tr("processing"))

    # --------------------------------------------------------------------------
    # ОСТАЛЬНЫЕ МЕТОДЫ
    # --------------------------------------------------------------------------
    
    def _set_action_state(self, state):
        try:
            self.action_btn.clicked.disconnect()
        except TypeError:
            pass

        if state == "idle":
            self.action_btn.setText(tr("btn_run"))
            self.action_btn.setEnabled(True)
            self.action_btn.setStyleSheet(STYLE_BTN_DARK)
            self.action_btn.clicked.connect(self.run_parser)
        elif state == "running":
            self.action_btn.setText(tr("btn_stop"))
            self.action_btn.setEnabled(True)
            self.action_btn.setStyleSheet(STYLE_BTN_DANGER)
            self.action_btn.clicked.connect(self.stop_parser)
        elif state == "single":
            self.action_btn.setText(tr("btn_running"))
            self.action_btn.setEnabled(False)
            self.action_btn.setStyleSheet(STYLE_BTN_DARK)
        elif state == "stopping":
            self.action_btn.setText(tr("btn_stopping"))
            self.action_btn.setEnabled(False)
            self.action_btn.setStyleSheet(STYLE_BTN_DARK)

    def _menu_open_file(self):
        self.mode_combo.setCurrentIndex(0)
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("menu_open_file"), "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.path_edit.setText(file_path)
            self._save_on_change()
            self.tabs.setCurrentIndex(1)
            self._start_quick_scan(file_path)

    def _menu_open_folder(self):
        self.mode_combo.setCurrentIndex(1)
        folder = QFileDialog.getExistingDirectory(self, tr("menu_open_folder"))
        if folder:
            self.path_edit.setText(folder)
            self._save_on_change()
            self.tabs.setCurrentIndex(1)
            self._start_quick_scan(folder)

    def browse_input(self):
        default_folder = self.settings.value("General/default_folder", "", type=str)
        if not (default_folder and os.path.isdir(default_folder)):
            default_folder = ""

        if self.is_batch_mode():
            folder = QFileDialog.getExistingDirectory(
                self, tr("menu_open_folder"), default_folder
            )
            if folder:
                self.path_edit.setText(folder)
                self._save_on_change()
                self.tabs.setCurrentIndex(1)
                self._start_quick_scan(folder)
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, tr("menu_open_file"), default_folder,
                "Text Files (*.txt);;All Files (*)"
            )
            if file_path:
                self.path_edit.setText(file_path)
                self._save_on_change()
                self.tabs.setCurrentIndex(1)
                self._start_quick_scan(file_path)

    def validate_inputs(self):
        path = self.path_edit.text()
        if not path:
            QMessageBox.warning(
                self, tr("error"),
                tr("warn_select_folder") if self.is_batch_mode() else tr("warn_select_file")
            )
            return False

        if self.is_batch_mode():
            if not os.path.isdir(path):
                QMessageBox.warning(self, tr("error"), tr("warn_invalid_folder"))
                return False
        else:
            if not os.path.exists(path):
                QMessageBox.warning(self, tr("error"), tr("warn_file_not_found"))
                return False
        return True

    def stop_parser(self):
        if self.worker and isinstance(self.worker, BatchWorker):
            self.worker.request_stop()
            self._set_action_state("stopping")
            self.append_to_console("")
            self.append_to_console(tr("console_stop_request"))
            self.status_bar.showMessage(tr("status_stop_request"))

    def update_batch_progress(self, current, total, filename):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.queue_label.setText(
            trf("queue_label", current=current, total=total, filename=filename)
        )

    def on_component_progress(self, text, percent):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(percent)
        self.queue_label.setText(text)

    def add_system_row(self, row):
        if "_update_excel_path" in row:
            r = self.systems_table.rowCount() - 1
            if r >= 0:
                item = self.systems_table.item(r, 0)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole + 2, row["_update_excel_path"])
            return

        if "_update_excel_path_all" in row:
            path = row["_update_excel_path_all"]
            for r in range(self.systems_table.rowCount()):
                item = self.systems_table.item(r, 0)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole + 2, path)
            return

        was_sorting = self.systems_table.isSortingEnabled()
        self.systems_table.setSortingEnabled(False)

        r = self.systems_table.rowCount()
        self.systems_table.insertRow(r)

        is_error = bool(row.get("_error"))

        name_item = QTableWidgetItem(row.get("name", ""))
        name_item.setData(Qt.ItemDataRole.UserRole + 1, row.get("log_path", ""))
        name_item.setData(Qt.ItemDataRole.UserRole + 2, "")
        self.systems_table.setItem(r, 0, name_item)

        model_item = QTableWidgetItem(row.get("model", ""))
        self.systems_table.setItem(r, 1, model_item)

        fw = row.get("fw", "")
        version = row.get("version", "")
        if fw and version:
            version_text = f"{fw} ({version})"
        elif version:
            version_text = version
        else:
            version_text = ""
        version_item = QTableWidgetItem(version_text)
        self.systems_table.setItem(r, 2, version_item)

        serial_item = QTableWidgetItem(row.get("serial", ""))
        self.systems_table.setItem(r, 3, serial_item)

        if is_error:
            comp_text = "ERROR"
        else:
            comp_text = str(row.get("components", ""))
        comp_item = QTableWidgetItem(comp_text)
        comp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.systems_table.setItem(r, 4, comp_item)

        if is_error:
            red = QColor(255, 80, 80)
            for col in range(5):
                item = self.systems_table.item(r, col)
                if item:
                    item.setForeground(red)

        self.systems_table.setSortingEnabled(was_sorting)
        self.systems_table.scrollToBottom()

    def _show_systems_context_menu(self, pos):
        item = self.systems_table.itemAt(pos)
        if item is None:
            return

        row_index = item.row()

        name_item = self.systems_table.item(row_index, 0)
        if name_item is None:
            return

        log_path = name_item.data(Qt.ItemDataRole.UserRole + 1) or ""
        excel_path = name_item.data(Qt.ItemDataRole.UserRole + 2) or ""

        system_name = name_item.text()
        serial_item = self.systems_table.item(row_index, 3)
        serial = serial_item.text() if serial_item else ""

        menu = QMenu(self)

        act_open_log = None
        act_open_excel = None

        if log_path and os.path.isdir(os.path.dirname(log_path)):
            act_open_log = menu.addAction(tr("ctx_open_log"))

        if excel_path and os.path.exists(excel_path):
            act_open_excel = menu.addAction(tr("ctx_open_excel"))

        if act_open_log or act_open_excel:
            menu.addSeparator()

        act_copy_name = menu.addAction(tr("ctx_copy_name"))
        act_copy_serial = menu.addAction(tr("ctx_copy_serial"))

        chosen = menu.exec(self.systems_table.viewport().mapToGlobal(pos))
        if chosen is None:
            return

        if chosen == act_open_log:
            self._open_folder(os.path.dirname(log_path))
        elif chosen == act_open_excel:
            self._open_folder(os.path.dirname(excel_path))
        elif chosen == act_copy_name:
            QApplication.clipboard().setText(system_name)
            self.status_bar.showMessage(trf("ctx_copied", text=system_name), 3000)
        elif chosen == act_copy_serial:
            QApplication.clipboard().setText(serial)
            self.status_bar.showMessage(trf("ctx_copied", text=serial), 3000)

    def _open_folder(self, folder):
        if not os.path.isdir(folder):
            QMessageBox.warning(
                self, tr("error"),
                trf("err_open_folder", e=f"Folder not found:\n{folder}")
            )
            return

        if not open_in_system(folder):
            QMessageBox.critical(
                self, tr("error"), trf("err_open_folder", e=folder)
            )

    def append_to_console(self, text):
        self.console.append(text)
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_current_tab(self):
        current = self.tabs.currentIndex()
        if current == 0:
            self.console.clear()
            self.status_bar.showMessage(tr("console_cleared"), 3000)
        elif current == 1:
            self.systems_table.setRowCount(0)
            self.status_bar.showMessage(tr("table_cleared"), 3000)

    def _show_export_menu(self):
        menu = QMenu(self)
        menu.addAction(tr("export_console"), self._export_console)
        menu.addAction(tr("export_systems"), self._export_systems)

        btn = self.export_btn
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        menu.exec(pos)

    def _export_console(self):
        text = self.console.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, tr("export_nothing_title"), tr("console_empty"))
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"console_{ts}.txt"

        path = self._pick_export_path(tr("export_console_title"), default_name, tr("export_filter_txt"))
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            QMessageBox.critical(self, tr("export_error"), trf("export_write_failed", e=e))
            return

        self._show_export_done(path)

    def _export_systems(self):
        rows = self.systems_table.rowCount()
        if rows == 0:
            QMessageBox.warning(self, tr("export_nothing_title"), tr("table_empty"))
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"systems_{ts}.csv"

        path = self._pick_export_path(tr("export_systems_title"), default_name, tr("export_filter_csv"))
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                headers = [self.systems_table.horizontalHeaderItem(c).text() for c in range(self.systems_table.columnCount())]
                writer.writerow(headers)
                for r in range(rows):
                    row_data = [self.systems_table.item(r, c).text() if self.systems_table.item(r, c) else "" for c in range(self.systems_table.columnCount())]
                    writer.writerow(row_data)
        except Exception as e:
            QMessageBox.critical(self, tr("export_error"), trf("export_write_failed", e=e))
            return

        self._show_export_done(path)

    def _pick_export_path(self, title, default_name, file_filter):
        export_folder = self.settings.value("General/export_folder", "", type=str)
        always_ask = self.settings.value("General/always_ask_export", True, type=bool)

        if not always_ask and export_folder and os.path.isdir(export_folder):
            return os.path.join(export_folder, default_name)

        if export_folder and os.path.isdir(export_folder):
            start_path = os.path.join(export_folder, default_name)
        else:
            start_path = default_name

        path, _ = QFileDialog.getSaveFileName(self, title, start_path, file_filter)
        return path or None

    def _show_export_done(self, path):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(tr("export_done_title"))
        msg.setText(trf("export_done_text", path=path))
        open_btn = msg.addButton(tr("export_open_folder"), QMessageBox.ButtonRole.ActionRole)
        msg.addButton(tr("ok"), QMessageBox.ButtonRole.AcceptRole)
        msg.exec()

        if msg.clickedButton() == open_btn:
            reveal_path(path)

        self.status_bar.showMessage(f"Exported: {os.path.basename(path)}", 5000)

    def on_finished(self, success, message, excel_path):
        self._set_action_state("idle")
        self.progress_bar.setVisible(False)
        self.queue_label.setText("")

        self.append_to_console("")
        self.append_to_console("=" * 60)

        if success:
            self.append_to_console(f"✓ {message}")
            self.append_to_console("=" * 60)
            self.status_bar.showMessage(message)

            if excel_path and os.path.exists(excel_path):
                self.last_excel_path = excel_path
                self.open_folder_btn.setEnabled(True)
                self.append_to_console(f"Excel report ready: {os.path.basename(excel_path)}")

                auto_open = self.settings.value("General/auto_open", False, type=bool)
                if auto_open:
                    if not open_in_system(excel_path):
                        self.append_to_console(f"Auto-open failed: {excel_path}")
        else:
            self.append_to_console(f"✗ {message}")
            self.append_to_console("=" * 60)
            self.status_bar.showMessage(tr("err_critical"))
            QMessageBox.critical(self, tr("error"), message)

    def open_result_folder(self):
        if not self.last_excel_path:
            QMessageBox.warning(self, tr("warning"), tr("err_no_result"))
            return

        folder_path = os.path.dirname(self.last_excel_path)
        if not os.path.exists(folder_path):
            QMessageBox.warning(self, tr("warning"), tr("err_folder_gone"))
            return

        if open_in_system(folder_path):
            self.status_bar.showMessage(trf("cli_opened", path=folder_path))
        else:
            QMessageBox.critical(self, tr("error"), trf("err_open_folder", e=folder_path))

    def _build_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu(tr("menu_file"))

        act_open_file = QAction(tr("menu_open_file"), self)
        act_open_file.setShortcut(QKeySequence("Ctrl+O"))
        act_open_file.triggered.connect(self._menu_open_file)
        file_menu.addAction(act_open_file)

        act_open_folder = QAction(tr("menu_open_folder"), self)
        act_open_folder.setShortcut(QKeySequence("Ctrl+Shift+O"))
        act_open_folder.triggered.connect(self._menu_open_folder)
        file_menu.addAction(act_open_folder)

        file_menu.addSeparator()

        act_open_result = QAction(tr("menu_open_result"), self)
        act_open_result.setShortcut(QKeySequence("Ctrl+R"))
        act_open_result.triggered.connect(self.open_result_folder)
        file_menu.addAction(act_open_result)

        file_menu.addSeparator()

        act_exit = QAction(tr("menu_exit"), self)
        act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        tools_menu = menubar.addMenu(tr("menu_tools"))

        act_detailed = QAction(tr("menu_detailed_analysis"), self)
        act_detailed.setShortcut(QKeySequence("Ctrl+D"))
        act_detailed.triggered.connect(self.show_detailed_analysis)
        tools_menu.addAction(act_detailed)

        tools_menu.addSeparator()

        act_settings = QAction(tr("menu_settings"), self)
        act_settings.triggered.connect(self.show_settings)
        tools_menu.addAction(act_settings)

        act_selftest = QAction(tr("menu_selftest"), self)
        act_selftest.setShortcut(QKeySequence("F5"))
        act_selftest.triggered.connect(self.run_self_test)
        tools_menu.addAction(act_selftest)

        help_menu = menubar.addMenu(tr("menu_help"))

        act_quickstart = QAction(tr("menu_quickstart"), self)
        act_quickstart.setShortcut(QKeySequence("F1"))
        act_quickstart.triggered.connect(self.show_quick_start)
        help_menu.addAction(act_quickstart)

        act_readme = QAction(tr("menu_readme"), self)
        act_readme.triggered.connect(self.open_readme)
        help_menu.addAction(act_readme)

        act_changelog = QAction(tr("menu_changelog"), self)
        act_changelog.triggered.connect(self.open_changelog)
        help_menu.addAction(act_changelog)

        help_menu.addSeparator()

        links_menu = help_menu.addMenu(tr("menu_useful_links"))
        for title, url in USEFUL_LINKS:
            act_link = QAction(title, self)
            act_link.triggered.connect(lambda checked=False, u=url: self._open_url(u))
            links_menu.addAction(act_link)

        help_menu.addSeparator()

        act_about = QAction(tr("menu_about"), self)
        act_about.triggered.connect(self.show_about)
        help_menu.addAction(act_about)

    def show_settings(self):
        dlg = SettingsDialog(self.settings, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.detailed_components = read_components()
            self.status_bar.showMessage(tr("settings_saved"), 3000)

    def show_detailed_analysis(self):
        current_path = self.path_edit.text().strip()
        file_paths = []
        if current_path:
            if os.path.isfile(current_path) and current_path.lower().endswith(".txt"):
                file_paths = [current_path]
            elif os.path.isdir(current_path):
                try:
                    file_paths = sorted([
                        os.path.join(current_path, f)
                        for f in os.listdir(current_path)
                        if f.lower().endswith(".txt") and os.path.isfile(os.path.join(current_path, f))
                    ])
                except Exception:
                    pass
        dlg = DetailedAnalysisDialog(self, current_path=current_path, file_paths=file_paths, selected_components=self.detailed_components)
        dlg.exec()
        self.detailed_components = dlg.selected_components

    def show_quick_start(self):
        supported_lines = [f"&nbsp;&nbsp;<b>{ver}</b> &mdash; {desc}" for ver, desc in SUPPORTED_VERSIONS_DESCRIPTION.items()]
        supported_html = "<br>".join(supported_lines)
        text = (
            f"<h3>{trf('qs_header', name=PARSER_NAME)}</h3>"
            f"<p>{tr('qs_step1')}</p><ul><li>{tr('qs_single_desc')}</li><li>{tr('qs_batch_desc')}</li></ul>"
            f"<p>{tr('qs_step2')}</p><p>{tr('qs_step3')}</p><p>{tr('qs_step4')}</p><hr>"
            f"<p>{tr('qs_supported')}</p><p>{supported_html}</p><p>{tr('qs_troubleshooting')}</p><hr><p>{tr('qs_footer')}</p>"
        )
        QMessageBox.information(self, tr("qs_title"), text)

    def open_readme(self):
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        readme_path = os.path.join(script_dir, "Docs", "README.txt")
        if not os.path.exists(readme_path):
            readme_path = os.path.join(script_dir, "README.txt")
        if not os.path.exists(readme_path):
            QMessageBox.warning(self, tr("error"), trf("err_readme_missing", path=readme_path))
            return
        if open_in_system(readme_path):
            self.status_bar.showMessage(trf("cli_opened", path=readme_path))
        else:
            QMessageBox.critical(self, tr("error"), trf("err_open_readme", e=readme_path))

    def open_changelog(self):
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(script_dir, "Docs", "CHANGELOG.txt")
        if not os.path.exists(path):
            QMessageBox.warning(self, tr("error"), trf("err_changelog_missing", path=path))
            return
        if open_in_system(path):
            self.status_bar.showMessage(trf("cli_opened", path=path))
        else:
            QMessageBox.critical(self, tr("error"), trf("err_open_changelog", e=path))

    def _open_url(self, url):
        if open_url(url):
            self.status_bar.showMessage(f"Opened in browser: {url}", 5000)
        else:
            QMessageBox.critical(self, tr("error"), trf("err_url", e=url))

    def run_self_test(self):
        test_file = self.path_edit.text().strip()
        if not (test_file and os.path.isfile(test_file) and test_file.lower().endswith(".txt")):
            test_file = None
        dlg = SelfTestDialog(self, test_file=test_file)
        dlg.exec()
        self.status_bar.showMessage(dlg.status_text)

    def show_about(self):
        text = trf("about_text", name=PARSER_NAME, version=PARSER_VERSION)
        QMessageBox.about(self, tr("about_title"), text)