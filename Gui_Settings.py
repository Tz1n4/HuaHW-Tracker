#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Settings.py — Settings dialog for Huawei Storage Log Parser.

Class SettingsDialog(QDialog):
- reads current values from QSettings,
- lets the user edit them,
- writes back on Save,
- "Reset to defaults" restores defaults (but does NOT save —
  the user must press Save after that).

Ключи QSettings:
    General/start_mode         "single" | "batch" | "last"
    General/default_folder     str (empty = use last_folder)
    General/export_folder      str
    General/always_ask_export  bool
    General/auto_open          bool
    General/include_synthetic  bool
    General/ask_customer       bool
    General/clear_console      bool
    General/clear_table        bool
    General/verbose_logging    bool
    General/language           "ru" | "en"
"""

import os
import sys
import subprocess

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QGroupBox, QRadioButton, QCheckBox, QLineEdit,
    QPushButton, QLabel, QButtonGroup, QFileDialog,
    QMessageBox, QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from Utils_Locale import (
    tr, trf,
    set_language, get_language,
    AVAILABLE_LANGUAGES, DEFAULT_LANGUAGE,
)


# ==============================================================================
# DEFAULTS
# ==============================================================================

DEFAULTS = {
    "start_mode":        "last",
    "default_folder":    "",
    "export_folder":     "",
    "always_ask_export": True,
    "auto_open":         False,
    "include_synthetic": False,
    "ask_customer":      True,
    "clear_console":     True,
    "clear_table":       True,
    "verbose_logging":   False,
    "language":          DEFAULT_LANGUAGE,
}


# ==============================================================================
# DIALOG
# ==============================================================================

class SettingsDialog(QDialog):
    """Settings dialog. Reads/writes via the passed QSettings instance."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(560)

        self._lang_at_open = self.settings.value(
            "General/language", DEFAULTS["language"], type=str
        )

        self._build_ui()
        self._load_from_settings()

    # --------------------------------------------------------------------------
    # UI
    # --------------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        general_box = QGroupBox(tr("settings_general"))
        general_layout = QVBoxLayout(general_box)

        mode_label = QLabel(tr("settings_start_mode"))
        mode_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        general_layout.addWidget(mode_label)

        self.mode_group = QButtonGroup(self)
        self.rb_single = QRadioButton(tr("settings_rb_single"))
        self.rb_batch  = QRadioButton(tr("settings_rb_batch"))
        self.rb_last   = QRadioButton(tr("settings_rb_last"))
        self.mode_group.addButton(self.rb_single)
        self.mode_group.addButton(self.rb_batch)
        self.mode_group.addButton(self.rb_last)

        general_layout.addWidget(self.rb_single)
        general_layout.addWidget(self.rb_batch)
        general_layout.addWidget(self.rb_last)

        general_layout.addSpacing(8)

        folder_label = QLabel(tr("settings_default_folder"))
        folder_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        general_layout.addWidget(folder_label)

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText(tr("settings_default_folder_ph"))
        folder_row.addWidget(self.folder_edit, 1)

        browse_btn = QPushButton(tr("browse"))
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse_btn)

        general_layout.addLayout(folder_row)

        general_layout.addSpacing(8)

        export_label = QLabel(tr("settings_export_folder"))
        export_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        general_layout.addWidget(export_label)

        export_row = QHBoxLayout()
        self.export_edit = QLineEdit()
        self.export_edit.setPlaceholderText(tr("settings_default_folder_ph"))
        export_row.addWidget(self.export_edit, 1)

        export_browse_btn = QPushButton(tr("browse"))
        export_browse_btn.clicked.connect(self._browse_export_folder)
        export_row.addWidget(export_browse_btn)

        general_layout.addLayout(export_row)

        self.cb_always_ask_export = QCheckBox(tr("settings_always_ask_export"))
        general_layout.addWidget(self.cb_always_ask_export)

        general_layout.addSpacing(8)

        lang_label = QLabel(tr("settings_language"))
        lang_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        general_layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        for code, name in AVAILABLE_LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        general_layout.addWidget(self.lang_combo)

        layout.addWidget(general_box)

        output_box = QGroupBox(tr("settings_output"))
        output_layout = QVBoxLayout(output_box)

        self.cb_auto_open = QCheckBox(tr("settings_auto_open"))
        output_layout.addWidget(self.cb_auto_open)

        self.cb_synthetic = QCheckBox(tr("settings_include_synthetic"))
        output_layout.addWidget(self.cb_synthetic)

        self.cb_ask_customer = QCheckBox(tr("settings_ask_customer"))
        output_layout.addWidget(self.cb_ask_customer)

        layout.addWidget(output_box)

        diag_box = QGroupBox(tr("settings_diagnostics"))
        diag_layout = QVBoxLayout(diag_box)

        self.cb_clear_console = QCheckBox(tr("settings_clear_console"))
        diag_layout.addWidget(self.cb_clear_console)

        self.cb_clear_table = QCheckBox(tr("settings_clear_table"))
        diag_layout.addWidget(self.cb_clear_table)

        self.cb_verbose = QCheckBox(tr("settings_verbose"))
        diag_layout.addWidget(self.cb_verbose)

        layout.addWidget(diag_box)

        btn_row = QHBoxLayout()

        self.reset_btn = QPushButton(tr("settings_reset"))
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        btn_row.addWidget(self.reset_btn)

        btn_row.addStretch(1)

        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton(tr("save"))
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_and_close)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    # --------------------------------------------------------------------------
    # LOAD / SAVE
    # --------------------------------------------------------------------------

    def _load_from_settings(self):
        """Reads current values from QSettings into the widgets."""
        s = self.settings

        start_mode = s.value("General/start_mode", DEFAULTS["start_mode"], type=str)
        if start_mode == "single":
            self.rb_single.setChecked(True)
        elif start_mode == "batch":
            self.rb_batch.setChecked(True)
        else:
            self.rb_last.setChecked(True)

        self.folder_edit.setText(
            s.value("General/default_folder", DEFAULTS["default_folder"], type=str)
        )
        self.export_edit.setText(
            s.value("General/export_folder", DEFAULTS["export_folder"], type=str)
        )

        self.cb_always_ask_export.setChecked(
            s.value("General/always_ask_export", DEFAULTS["always_ask_export"], type=bool)
        )
        self.cb_auto_open.setChecked(
            s.value("General/auto_open", DEFAULTS["auto_open"], type=bool)
        )
        self.cb_synthetic.setChecked(
            s.value("General/include_synthetic", DEFAULTS["include_synthetic"], type=bool)
        )
        self.cb_ask_customer.setChecked(
            s.value("General/ask_customer", DEFAULTS["ask_customer"], type=bool)
        )
        self.cb_clear_console.setChecked(
            s.value("General/clear_console", DEFAULTS["clear_console"], type=bool)
        )
        self.cb_clear_table.setChecked(
            s.value("General/clear_table", DEFAULTS["clear_table"], type=bool)
        )
        self.cb_verbose.setChecked(
            s.value("General/verbose_logging", DEFAULTS["verbose_logging"], type=bool)
        )

        cur_lang = s.value("General/language", DEFAULTS["language"], type=str)
        idx = self.lang_combo.findData(cur_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

    def _save_and_close(self):
        """Writes all values back to QSettings and closes the dialog."""
        s = self.settings

        if self.rb_single.isChecked():
            s.setValue("General/start_mode", "single")
        elif self.rb_batch.isChecked():
            s.setValue("General/start_mode", "batch")
        else:
            s.setValue("General/start_mode", "last")

        s.setValue("General/default_folder", self.folder_edit.text().strip())
        s.setValue("General/export_folder", self.export_edit.text().strip())
        s.setValue("General/always_ask_export", self.cb_always_ask_export.isChecked())

        s.setValue("General/auto_open", self.cb_auto_open.isChecked())
        s.setValue("General/include_synthetic", self.cb_synthetic.isChecked())
        s.setValue("General/ask_customer", self.cb_ask_customer.isChecked())
        s.setValue("General/clear_console", self.cb_clear_console.isChecked())
        s.setValue("General/clear_table", self.cb_clear_table.isChecked())
        s.setValue("General/verbose_logging", self.cb_verbose.isChecked())

        new_lang = self.lang_combo.currentData() or DEFAULTS["language"]
        s.setValue("General/language", new_lang)

        s.sync()

        if new_lang != self._lang_at_open:
            self._offer_restart(new_lang)

        self.accept()

    # --------------------------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------------------------

    def _browse_folder(self):
        """Pick a default folder."""
        current = self.folder_edit.text().strip()
        if not current or not os.path.isdir(current):
            current = ""

        folder = QFileDialog.getExistingDirectory(
            self, tr("settings_select_default_folder"), current
        )
        if folder:
            self.folder_edit.setText(folder)

    def _browse_export_folder(self):
        """Pick a default export folder."""
        current = self.export_edit.text().strip()
        if not current or not os.path.isdir(current):
            current = ""

        folder = QFileDialog.getExistingDirectory(
            self, tr("settings_select_export_folder"), current
        )
        if folder:
            self.export_edit.setText(folder)

    def _reset_to_defaults(self):
        """Restores widgets to default values (without saving)."""
        answer = QMessageBox.question(
            self, tr("settings_reset_title"),
            tr("settings_reset_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        if DEFAULTS["start_mode"] == "single":
            self.rb_single.setChecked(True)
        elif DEFAULTS["start_mode"] == "batch":
            self.rb_batch.setChecked(True)
        else:
            self.rb_last.setChecked(True)

        self.folder_edit.setText(DEFAULTS["default_folder"])
        self.export_edit.setText(DEFAULTS["export_folder"])
        self.cb_always_ask_export.setChecked(DEFAULTS["always_ask_export"])
        self.cb_auto_open.setChecked(DEFAULTS["auto_open"])
        self.cb_synthetic.setChecked(DEFAULTS["include_synthetic"])
        self.cb_ask_customer.setChecked(DEFAULTS["ask_customer"])
        self.cb_clear_console.setChecked(DEFAULTS["clear_console"])
        self.cb_clear_table.setChecked(DEFAULTS["clear_table"])
        self.cb_verbose.setChecked(DEFAULTS["verbose_logging"])

        idx = self.lang_combo.findData(DEFAULTS["language"])
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

    # --------------------------------------------------------------------------
    # RESTART PROMPT
    # --------------------------------------------------------------------------

    def _offer_restart(self, new_lang):
        """Спрашивает, перезапустить ли приложение для применения языка."""
        answer = QMessageBox.question(
            self,
            tr("settings_restart_title"),
            tr("settings_restart_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            if sys.platform == "win32":
                subprocess.Popen([sys.executable] + sys.argv)
                sys.exit(0)
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            QMessageBox.warning(
                self, tr("error"),
                f"Failed to restart automatically: {e}\n\n"
                f"Please restart the application manually."
            )