#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Dialog_Detailed_Analysis.py — окна для детального анализа оборудования.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, 
    QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from Utils.Utils_Locale import tr


class ComponentSelectionDialog(QDialog):
    """Окно со списком компонентов и галочками."""

    def __init__(self, current_selected, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор компонентов")
        self.setMinimumSize(350, 400)

        self.current_selected = set(current_selected)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("Отметьте компоненты, которые нужно анализировать:")
        lbl.setStyleSheet("color: #aaa;")
        layout.addWidget(lbl)

        select_btn_layout = QHBoxLayout()
        
        btn_select_all = QPushButton("Выбрать все")
        btn_select_all.setStyleSheet(self._btn_style_small())
        btn_select_all.clicked.connect(lambda: self._toggle_all(True))
        select_btn_layout.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("Снять все")
        btn_deselect_all.setStyleSheet(self._btn_style_small())
        btn_deselect_all.clicked.connect(lambda: self._toggle_all(False))
        select_btn_layout.addWidget(btn_deselect_all)
        
        select_btn_layout.addStretch(1)
        layout.addLayout(select_btn_layout)

        self.components_list = QListWidget()
        self.components_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
            }
            QListWidget::item { padding: 4px; }
        """)
        
        all_components = [
            "Controller", "Disk", "Power Supply", "BBU", "Fan", 
            "I/O Module", "Expansion Board", "SFP Module", "Enclosure"
        ]
        
        for comp in all_components:
            item = QListWidgetItem(comp)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if comp in self.current_selected:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.components_list.addItem(item)

        layout.addWidget(self.components_list, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.setStyleSheet(self._btn_style_dark())
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("Применить")
        ok_btn.setStyleSheet(self._btn_style_primary())
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

    def _toggle_all(self, state: bool):
        check_state = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        for i in range(self.components_list.count()):
            item = self.components_list.item(i)
            item.setCheckState(check_state)

    def get_selected(self):
        selected = []
        for i in range(self.components_list.count()):
            item = self.components_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

    def _btn_style_small(self):
        return """
            QPushButton {
                background-color: #2d2d2d; color: #d4d4d4;
                border: 1px solid #555555; border-radius: 3px;
                padding: 4px 10px;
            }
            QPushButton:hover { background-color: #3d3d3d; }
        """

    def _btn_style_dark(self):
        return """
            QPushButton {
                background-color: #2d2d2d; color: #d4d4d4;
                border: 1px solid #555555; border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #3d3d3d; }
        """

    def _btn_style_primary(self):
        return """
            QPushButton {
                background-color: #2196F3; color: #FFFFFF;
                border: 1px solid #2196F3; border-radius: 5px;
                padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """


class DetailedAnalysisDialog(QDialog):
    """Главное окно детального анализа оборудования."""

    def __init__(self, parent=None, current_path="", file_paths=None, selected_components=None):
        super().__init__(parent)
        self.setWindowTitle(tr("detailed_analysis_title"))
        self.setMinimumSize(1100, 600)
        self.current_path = current_path
        self.file_paths = file_paths or []

        if selected_components is not None:
            self.selected_components = list(selected_components)
        else:
            self.selected_components = [
                "Controller", "Disk", "Power Supply", "BBU", "Fan", 
                "I/O Module", "Expansion Board", "SFP Module", "Enclosure"
            ]

        self._last_bbu_data = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        header = QLabel(tr("detailed_analysis_title"))
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        hint = QLabel(tr("detailed_analysis_placeholder"))
        hint.setStyleSheet("color: #888;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        source_row = QHBoxLayout()
        source_label = QLabel("Выбранный объект:")
        source_label.setStyleSheet("color: #aaa; font-weight: bold;")
        source_row.addWidget(source_label)

        self.lbl_source_path = QLabel(self._format_source_path())
        self.lbl_source_path.setStyleSheet("color: #e0e0e0;")
        self.lbl_source_path.setWordWrap(True)
        source_row.addWidget(self.lbl_source_path, 1)
        layout.addLayout(source_row)

        config_group = QGroupBox("Параметры анализа")
        config_layout = QVBoxLayout(config_group)

        select_row = QHBoxLayout()
        self.btn_select_components = QPushButton("Выбрать компоненты...")
        self.btn_select_components.setStyleSheet(self._btn_style_dark())
        self.btn_select_components.clicked.connect(self._open_selection_dialog)
        select_row.addWidget(self.btn_select_components)

        select_row.addSpacing(10)

        self.lbl_selected_summary = QLabel()
        self.lbl_selected_summary.setStyleSheet("color: #aaa;")
        self.lbl_selected_summary.setWordWrap(True)
        select_row.addWidget(self.lbl_selected_summary, 1)

        config_layout.addLayout(select_row)
        layout.addWidget(config_group)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 8px 16px;
                border: 1px solid #3c3c3c;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #2196F3;
            }
        """)
        layout.addWidget(self.tabs, 1)

        btn_row = QHBoxLayout()
        
        self.btn_run_analysis = QPushButton("Запустить анализ")
        self.btn_run_analysis.setStyleSheet(self._btn_style_primary())
        self.btn_run_analysis.setEnabled(False)
        self.btn_run_analysis.clicked.connect(self._on_run_clicked)
        btn_row.addWidget(self.btn_run_analysis)

        self.btn_export_excel = QPushButton("📤 Экспорт в Excel")
        self.btn_export_excel.setStyleSheet(self._btn_style_dark())
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.clicked.connect(self._export_to_excel)
        btn_row.addWidget(self.btn_export_excel)

        btn_row.addStretch(1)

        close_btn = QPushButton(tr("close"))
        close_btn.setStyleSheet(self._btn_style_dark())
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)
        self._update_summary_label()

    def _format_source_path(self):
        if not self.current_path:
            return f"<i>{tr('analysis_no_source')}</i>"
        name = os.path.basename(os.path.normpath(self.current_path))
        if os.path.isdir(self.current_path):
            return f"<b>{name}</b> ({tr('analysis_folder')})<br><span style='color:#888;'>{self.current_path}</span>"
        else:
            return f"<b>{name}</b> ({tr('analysis_file')})<br><span style='color:#888;'>{self.current_path}</span>"

    def _open_selection_dialog(self):
        dlg = ComponentSelectionDialog(self.selected_components, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.selected_components = dlg.get_selected()
            self._update_summary_label()

    def _update_summary_label(self):
        count = len(self.selected_components)
        if count == 0:
            self.lbl_selected_summary.setText("<b>Компоненты не выбраны</b>")
            self.btn_run_analysis.setEnabled(False)
        else:
            display_list = ", ".join(self.selected_components[:4])
            if count > 4:
                display_list += f" и еще {count - 4}..."
            self.lbl_selected_summary.setText(f"<b>Выбрано ({count}):</b> {display_list}")
            self.btn_run_analysis.setEnabled(bool(self.file_paths))

    def _on_run_clicked(self):
        if not self.file_paths:
            QMessageBox.warning(self, "Ошибка", "Нет файлов для анализа.")
            return

        self.tabs.clear()
        analyzed_anything = False
        unsupported_components = []

        if "BBU" in self.selected_components:
            self._analyze_bbu()
            analyzed_anything = True

        supported_now = {"BBU"}
        for comp in self.selected_components:
            if comp not in supported_now:
                unsupported_components.append(comp)

        if not analyzed_anything:
            QMessageBox.information(
                self, "Анализ", 
                f"Логика анализа для выбранных компонентов пока не написана:\n{', '.join(unsupported_components)}"
            )
        elif unsupported_components:
            QMessageBox.information(
                self, "Внимание", 
                f"Анализ выполнен только для поддерживаемых компонентов (BBU).\n"
                f"Следующие компоненты проигнорированы: {', '.join(unsupported_components)}"
            )

    def _analyze_bbu(self):
        from Parsers.Parsers_Details.Parser_BBU_Details import parse_bbu_details
        from Core.Core_System_Info import parse_system_info
        
        all_bbu_data = []
        
        for fpath in self.file_paths:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                sys_info = parse_system_info(content[:5000])
                sys_name = sys_info.get("name", os.path.basename(fpath))
                sys_model = sys_info.get("model", "N/A")
                sys_version = sys_info.get("version", "V3")
                
                bbu_list = parse_bbu_details(content, sys_version=sys_version)
                
                for bbu in bbu_list:
                    bbu["sys_name"] = sys_name
                    bbu["sys_model"] = sys_model
                    all_bbu_data.append(bbu)
            except Exception as e:
                print(f"Ошибка при чтении {fpath}: {e}")

        if not all_bbu_data:
            return

        # Сохраняем данные для экспорта и включаем кнопку
        self._last_bbu_data = all_bbu_data
        self.btn_export_excel.setEnabled(True)

        bbu_tab = QWidget()
        tab_layout = QVBoxLayout(bbu_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e; color: #d4d4d4;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d; color: #d4d4d4;
                border: 1px solid #3c3c3c; padding: 4px;
            }
        """)

        headers = [
            "Система", "Модель СХД", "ID (Слот)", "Здоровье", "Статус", "Напряжение", 
            "Остаток (дн. из лога)", "Остаток на сегодня (дн.)", "Конец срока", 
            "Поставка", "Возраст", "Part Number", "Серийный номер"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(all_bbu_data))

        table.setSortingEnabled(False)

        for row, bbu in enumerate(all_bbu_data):
            days_left = bbu["real_remain_days"]
            row_color = None
            if isinstance(days_left, int):
                if days_left < 0:
                    row_color = QColor(255, 80, 80)
                elif days_left < 180:
                    row_color = QColor(255, 180, 50)

            age_str = str(bbu.get("age_days", "N/A"))
            if isinstance(bbu.get("age_days"), int):
                age_years = bbu["age_days"] // 365
                age_rem_days = bbu["age_days"] % 365
                if age_years > 0:
                    age_str = f"{age_years} г. {age_rem_days} дн."
                else:
                    age_str = f"{age_rem_days} дн."

            values = [
                bbu["sys_name"], bbu["sys_model"], bbu["id"], bbu["health"], 
                bbu["running"], bbu["voltage"], bbu["remain_life_log"], str(days_left), 
                bbu["end_of_life"], bbu["delivered_on"], age_str, bbu["item"], bbu["barcode"]
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                
                if col in (2, 3, 6, 7):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                if row_color:
                    item.setForeground(row_color)
                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        table.setSortingEnabled(True)
        
        tab_layout.addWidget(table)
        self.tabs.addTab(bbu_tab, "🔋 BBU")
        self.tabs.setCurrentIndex(0)

    def _export_to_excel(self):
        if not self._last_bbu_data:
            QMessageBox.warning(self, "Экспорт", "Нет данных для экспорта. Сначала запустите анализ.")
            return

        from Core.Core_Export_Excel_Details import DetailsExcelExporter

        if os.path.isdir(self.current_path):
            output_dir = self.current_path
        else:
            output_dir = os.path.dirname(self.current_path)

        if self._last_bbu_data and self._last_bbu_data[0].get("sys_name") != "N/A":
            name_hint = self._last_bbu_data[0]["sys_name"]
            if len(self.file_paths) > 1:
                name_hint = "нескольких_СХД"
        else:
            name_hint = os.path.splitext(os.path.basename(self.current_path))[0]
            if not name_hint:
                name_hint = "СХД"

        name_hint = "".join([c for c in name_hint if c.isalnum() or c in " -_"]).strip()

        try:
            exporter = DetailsExcelExporter()
            result_path = exporter.export_bbu(
                bbu_data=self._last_bbu_data,
                output_dir=output_dir,
                name_hint=name_hint
            )
            
            # --- ДОБАВЛЯЕМ АВТООТКРЫТИЕ ---
            if self.parent() and hasattr(self.parent(), "settings"):
                auto_open = self.parent().settings.value("General/auto_open_details", False, type=bool)
                if auto_open:
                    from Utils.Utils_System import open_in_system
                    open_in_system(result_path)

            QMessageBox.information(
                self, "Экспорт завершён",
                f"Файл успешно сохранён:\n{result_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка экспорта", 
                f"Не удалось сохранить файл:\n{e}"
            )

    def _btn_style_dark(self):
        return """
            QPushButton {
                background-color: #2d2d2d; color: #d4d4d4;
                border: 1px solid #555555; border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #3d3d3d; }
        """

    def _btn_style_primary(self):
        return """
            QPushButton {
                background-color: #2196F3; color: #FFFFFF;
                border: 1px solid #2196F3; border-radius: 5px;
                padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled {
                background-color: #1e1e1e; color: #666666;
                border: 1px solid #333333;
            }
        """