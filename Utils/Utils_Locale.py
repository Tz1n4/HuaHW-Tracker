#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils_Locale.py — локализация UI (EN / RU).

ВАЖНО:
- Здесь только UI-строки (кнопки, меню, заголовки, диалоги).
- Строки-ДАННЫЕ отчёта (TEXT_MEMORY, TEXT_SYSTEM_DISK, TEXT_NO_DESCRIPTION,
  TEXT_SFP_NO_BOM_TEMPLATE, категории TYPE_TO_CATEGORY) остаются в
  Utils_Constants.py и НЕ переводятся — они уходят в Excel.

Использование:
    from Utils.Utils_Locale import tr, trf, set_language, get_language

    btn = QPushButton(tr("btn_run"))
    label = trf("queue_label", current=1, total=10, filename="log.txt")
"""


# ==============================================================================
# ТЕКУЩИЙ ЯЗЫК
# ==============================================================================

AVAILABLE_LANGUAGES = {
    "en": "English",
    "ru": "Русский",
}

DEFAULT_LANGUAGE = "ru"

_current_lang = DEFAULT_LANGUAGE


def set_language(lang: str) -> None:
    """Устанавливает текущий язык. Неизвестный код → DEFAULT_LANGUAGE."""
    global _current_lang
    _current_lang = lang if lang in AVAILABLE_LANGUAGES else DEFAULT_LANGUAGE


def get_language() -> str:
    """Возвращает текущий код языка ('en' / 'ru')."""
    return _current_lang


# ==============================================================================
# СЛОВАРИ
# ==============================================================================

STRINGS = {

    # ==========================================================================
    # ENGLISH
    # ==========================================================================

    "en": {
        # --- Общие ---
        "app_title":            "{name} — GUI v{version}",
        "ready":                "Ready",
        "processing":           "Processing...",
        "settings_saved":       "Settings saved",
        "error":                "Error",
        "warning":              "Warning",
        "info":                 "Information",
        "ok":                   "OK",
        "cancel":               "Cancel",
        "save":                 "Save",
        "browse":               "Browse",
        "close":                "Close",

        # --- Кнопки главного окна ---
        "btn_single_mode":      "Single File",
        "btn_batch_mode":       "Folder (Batch)",
        "btn_browse_file":      "Browse",
        "btn_browse_folder":    "📂 Select Folder",
        "btn_run":              "▶ Run Parser",
        "btn_stop":             "⏹ Stop",
        "btn_running":          "⏳ Running...",
        "btn_stopping":         "⏳ Stopping...",
        "btn_open_result":      "📁 Open Result",
        "btn_clear":            "🗑 Clear",
        "btn_export":           "📤 Export",

        # --- Метки / placeholder ---
        "label_log_file":       "Log File:",
        "label_log_folder":     "Log Folder:",
        "placeholder_file":     "Select log file (.txt)...",
        "placeholder_folder":   "Select folder with .txt logs...",
        "mode_single":          "Single file mode",
        "mode_batch":           "Batch mode: Processing entire folder sequentially",

        # --- Вкладки ---
        "tab_console":          "📋 Console",
        "tab_systems":          "📊 Systems",

        # --- Таблица Systems ---
        "col_sys_name":         "System Name",
        "col_model":            "Model",
        "col_version":          "Version",
        "col_serial":           "Serial",
        "col_components":       "Components",

        # --- Меню ---
        "menu_file":            "&File",
        "menu_tools":           "&Tools",
        "menu_help":            "&Help",
        "menu_open_file":       "Open Log File...",
        "menu_open_folder":     "Open Folder...",
        "menu_open_result":     "Open Result Folder",
        "menu_exit":            "Exit",
        "menu_selftest":        "Self-test...",
        "menu_settings":        "Settings...",
        "menu_detailed_analysis": "Detailed Equipment Analysis\tCtrl+D",
        "menu_quickstart":      "Quick Start",
        "menu_readme":          "Open README",
        "menu_changelog":       "Open Changelog",
        "menu_useful_links":    "Useful Links",
        "menu_about":           "About",

        # --- Валидация ---
        "warn_select_file":     "Please select a log file!",
        "warn_select_folder":   "Please select a folder!",
        "warn_invalid_folder":  "Invalid folder path!",
        "warn_file_not_found":  "Log file not found!",

        # --- Прогресс / консоль ---
        "queue_label":          "Queue: {current}/{total} — Current: {filename}",
        "console_start_batch":  "Starting BATCH processing...",
        "console_start_single": "Starting single file parsing...",
        "console_folder":       "Folder: {path}",
        "console_file":         "File: {path}",
        "console_stop_request": "⏹ Stop requested — finishing current file...",
        "status_stop_request":  "Stop requested...",
        "console_cleared":      "Console cleared",
        "table_cleared":        "Systems table cleared",
        "console_empty":        "Console is empty.",
        "table_empty":          "Systems table is empty.",

        # --- Меню экспорта ---
        "export_console":       "📄  Console → .txt",
        "export_systems":       "📊  Systems → .csv",
        "export_console_title": "Save Console as",
        "export_systems_title": "Save Systems as",
        "export_filter_txt":    "Text files (*.txt)",
        "export_filter_csv":    "CSV files (*.csv)",
        "export_done_title":    "Export complete",
        "export_done_text":     "File saved to:\n{path}",
        "export_open_folder":   "Open Folder",
        "export_error":         "Export error",
        "export_write_failed":  "Failed to write file:\n{e}",
        "export_nothing_title": "Nothing to export",

        # --- Context menu Systems ---
        "ctx_open_log":         "📁  Open log folder",
        "ctx_open_excel":       "📊  Open Excel report folder",
        "ctx_copy_name":        "📋  Copy system name",
        "ctx_copy_serial":      "📋  Copy serial number",
        "ctx_copied":           "Copied: {text}",

        # --- Ошибки ---
        "err_folder_gone":      "Folder no longer exists!",
        "err_no_result":        "No result available yet!",
        "err_open_folder":      "Failed to open folder:\n{e}",
        "err_open_readme":      "Failed to open README: {e}",
        "err_open_changelog":   "Failed to open CHANGELOG: {e}",
        "err_readme_missing":   "README.txt not found next to the script:\n{path}",
        "err_changelog_missing":"CHANGELOG.txt not found next to the script:\n{path}",
        "err_url":              "Failed to open URL:\n{e}",
        "err_critical":         "Error occurred",
        "err_selftest":         "Self-test error",
        "err_drop_unsupported": "Only .txt files or folders are supported.",

        # --- Окно Settings ---
        "settings_title":       "Settings",
        "settings_general":     "General",
        "settings_output":      "Output",
        "settings_diagnostics": "Diagnostics",
        "settings_start_mode":  "Start mode:",
        "settings_rb_single":   "Single File",
        "settings_rb_batch":    "Folder (Batch)",
        "settings_rb_last":     "Last used",
        "settings_default_folder":        "Default folder for Open dialogs:",
        "settings_default_folder_ph":     "(empty = use last opened folder)",
        "settings_export_folder":         "Default folder for exported files:",
        "settings_always_ask_export":     "Always ask for export location",
        "settings_auto_open":             "Auto-open Excel after creation",
        "settings_include_synthetic":     "Include synthetic rows (Memory / System Disk Drive)",
        "settings_clear_console":         "Clear console on new run",
        "settings_clear_table":           "Clear Systems table on new run",
        "settings_verbose":               "Verbose logging",
        "settings_language":              "Language:",
        "settings_reset":                 "Reset to defaults",
        "settings_reset_title":           "Reset to defaults",
        "settings_reset_text":            "Reset all settings to their default values?\n\nNothing is saved until you press Save.",
        "settings_select_default_folder": "Select Default Folder",
        "settings_select_export_folder":  "Select Default Export Folder",
        "settings_restart_title":         "Language changed",
        "settings_restart_text":          "The interface language will change after restarting the application.\n\nRestart now?",

        # --- Окно Customer / Project ---
        "cust_dialog_title":    "Customer & Project",
        "cust_dialog_header":   "Enter customer and project info",
        "cust_dialog_hint":     "These values will be written into columns B and C\nof every row in the Excel report.",
        "cust_label_customer":  "Customer (CRM2):",
        "cust_label_project":   "Project (CRM2):",
        "cust_ph_customer":     "e.g. PJSC Rostelecom",
        "cust_ph_project":      "e.g. DataCenter-MSK-2026",
        "cust_continue":        "Continue",
        "settings_ask_customer": "Ask for Customer / Project before run",

        # --- Окно «Детальный анализ оборудования» ---
        "detailed_analysis_title":       "Detailed Equipment Analysis",
        "detailed_analysis_placeholder": "This section is under development. The analysis logic will be added here.",
        "analysis_no_source":            "No file or folder selected",
        "analysis_folder":               "folder",
        "analysis_file":                 "file",

        # --- Окно Self-test ---
        "selftest_title":       "Self-test",
        "selftest_result":      "Result: {ok} OK, {fail} FAIL",
        "selftest_copy":        "📋 Copy to clipboard",
        "selftest_status":      "Self-test: {ok} OK, {fail} FAIL",

        # --- About ---
        "about_title":          "About",
        "about_text": (
            "<h3>{name}</h3>"
            "<p><b>Version:</b> {version}</p>"
            "<p>Parser for Huawei Storage logs (V6, V5, V3).<br>"
            "Generates Excel reports in ZIP (spare parts) form.</p>"
            "<hr>"
            "<p><b>Developed by:</b> Daniil Barinshtein<br>"
            "<b>Contact:</b> Tg: @Tz1n4</p>"
            "<hr>"
            "<p>© 2026</p>"
        ),

        # --- Quick Start ---
        "qs_title":             "Quick Start",
        "qs_header":            "{name} — Quick Start",
        "qs_step1":             "<b>1. Choose mode</b>",
        "qs_single_desc":       "<b>Single File</b> — parse one .txt log",
        "qs_batch_desc":        "<b>Folder (Batch)</b> — parse all .txt logs in a folder, combine into one Excel report",
        "qs_step2":             "<b>2. Select path</b> — click Browse or drag &amp; drop a file/folder.",
        "qs_step3":             "<b>3. Click Run Parser</b> — the Excel report (ЗИП form) is created next to the log (or in the folder in batch mode).",
        "qs_step4":             "<b>4. Open Result Folder</b> — jump to the report location.",
        "qs_supported":         "<b>Supported systems:</b>",
        "qs_troubleshooting":   "<b>Troubleshooting:</b> if a component shows <i>\"Описание отсутствует, требуется проверка в Spare Query\"</i>, the Elabel section for that component is empty in the log — check Spare Query manually.",
        "qs_footer":            "Press <b>F5</b> for Self-test, <b>F1</b> to reopen this window.",

        # --- CLI ---
        "cli_usage_title":      "Usage:",
        "cli_usage_gui":        "  python Main.py                       → launch GUI",
        "cli_usage_single":     "  python Main.py log.txt               → single mode (one file)",
        "cli_usage_batch":      "  python Main.py C:\\Logs               → batch mode (folder)",
        "cli_usage_batch_force":"  python Main.py --batch C:\\Logs       → force batch mode",
        "cli_usage_options_title": "Options:",
        "cli_usage_customer":   '  --customer "Name"                    → set customer (CRM2, column B)',
        "cli_usage_project":    '  --project "Name"                     → set project (CRM2, column C)',
        "cli_customer":         "Customer:   {customer}",
        "cli_project":          "Project:    {project}",
        "cli_err_missing_value":"Error: {flag} requires a value.",
        "cli_special_title":    "Special commands:",
        "cli_help":             "  python Main.py --help, -h            → show this help",
        "cli_readme":           "  python Main.py --readme              → open README.txt",
        "cli_selftest":         "  python Main.py --selftest            → run self-test in console",
        "cli_changelog":        "  python Main.py --changelog           → open CHANGELOG.txt",
        "cli_err_no_path":      "Error: no path provided.",
        "cli_err_path_not_found":"Error: path not found: {path}",
        "cli_err_batch_needs_dir":"Error: --batch requires a folder, got file: {path}",
        "cli_err_not_folder":   "Error: not a folder: {path}",
        "cli_err_no_txt":       "Error: no .txt files found in {path}",
        "cli_warn_not_txt":     "Warning: file doesn't look like .txt: {path}",
        "cli_warn_unexpected":  "Warning: unexpected argument ignored: {arg}",
        "cli_reading_file":     "Reading file: {path}",
        "cli_system":           "System:     {name}",
        "cli_model":            "Model:      {model}",
        "cli_serial":           "Serial:     {serial}",
        "cli_version":          "Version:    {version}",
        "cli_components":       "Components: {n}",
        "cli_generating":       "Generating Excel...",
        "cli_excel_created":    "Excel created: {path}",
        "cli_found_files":      "Found {n} .txt file(s) in folder",
        "cli_processing":       ">>> Processing [{idx}/{total}]: {name}",
        "cli_ok":               "    OK: {name} ({n} components)",
        "cli_skip":             "    SKIP: {e}",
        "cli_no_success":       "Error: no logs were parsed successfully ({n} errors).",
        "cli_generating_batch": "Generating combined Excel...",
        "cli_parsed_summary":   "Parsed: {ok}/{total}",
        "cli_errors_suffix":    ", errors: {n}",
        "cli_selftest_header":  "SELF-TEST",
        "cli_selftest_result":  "Result: {ok} OK, {fail} FAIL",
        "cli_selftest_module_missing":"Error: Utils_SelfTest module not found.",
        "cli_opened":           "Opened: {path}",
        "cli_err_open":         "Error: failed to open {what}: {e}",
    },

    # ==========================================================================
    # РУССКИЙ
    # ==========================================================================

    "ru": {
        # --- Общие ---
        "app_title":            "{name} — GUI v{version}",
        "ready":                "Готово",
        "processing":           "Обработка...",
        "settings_saved":       "Настройки сохранены",
        "error":                "Ошибка",
        "warning":              "Предупреждение",
        "info":                 "Информация",
        "ok":                   "ОК",
        "cancel":               "Отмена",
        "save":                 "Сохранить",
        "browse":               "Обзор",
        "close":                "Закрыть",

        # --- Кнопки главного окна ---
        "btn_single_mode":      "Один файл",
        "btn_batch_mode":       "Папка (пакетно)",
        "btn_browse_file":      "Обзор",
        "btn_browse_folder":    "📂 Выбрать папку",
        "btn_run":              "▶ Запустить",
        "btn_stop":             "⏹ Остановить",
        "btn_running":          "⏳ Выполняется...",
        "btn_stopping":         "⏳ Остановка...",
        "btn_open_result":      "📁 Открыть результат",
        "btn_clear":            "🗑 Очистить",
        "btn_export":           "📤 Экспорт",

        # --- Метки / placeholder ---
        "label_log_file":       "Лог-файл:",
        "label_log_folder":     "Папка с логами:",
        "placeholder_file":     "Выберите лог-файл (.txt)...",
        "placeholder_folder":   "Выберите папку с .txt логами...",
        "mode_single":          "Режим одного файла",
        "mode_batch":           "Пакетный режим: последовательная обработка всей папки",

        # --- Вкладки ---
        "tab_console":          "📋 Консоль",
        "tab_systems":          "📊 Системы",

        # --- Таблица Systems ---
        "col_sys_name":         "Имя системы",
        "col_model":            "Модель",
        "col_version":          "Версия",
        "col_serial":           "Серийный номер",
        "col_components":       "Компонентов",

        # --- Меню ---
        "menu_file":            "&Файл",
        "menu_tools":           "&Инструменты",
        "menu_help":            "&Справка",
        "menu_open_file":       "Открыть лог-файл...",
        "menu_open_folder":     "Открыть папку...",
        "menu_open_result":     "Открыть папку с результатом",
        "menu_exit":            "Выход",
        "menu_selftest":        "Self-test...",
        "menu_settings":        "Настройки...",
        "menu_detailed_analysis": "Детальный анализ оборудования\tCtrl+D",
        "menu_quickstart":      "Быстрый старт",
        "menu_readme":          "Открыть README",
        "menu_changelog":       "Открыть CHANGELOG",
        "menu_useful_links":    "Полезные ссылки",
        "menu_about":           "О программе",

        # --- Валидация ---
        "warn_select_file":     "Выберите лог-файл!",
        "warn_select_folder":   "Выберите папку!",
        "warn_invalid_folder":  "Некорректный путь к папке!",
        "warn_file_not_found":  "Лог-файл не найден!",

        # --- Прогресс / консоль ---
        "queue_label":          "Очередь: {current}/{total} — Текущий: {filename}",
        "console_start_batch":  "Запуск ПАКЕТНОЙ обработки...",
        "console_start_single": "Запуск обработки одного файла...",
        "console_folder":       "Папка: {path}",
        "console_file":         "Файл: {path}",
        "console_stop_request": "⏹ Запрошена остановка — завершаем текущий файл...",
        "status_stop_request":  "Запрошена остановка...",
        "console_cleared":      "Консоль очищена",
        "table_cleared":        "Таблица Systems очищена",
        "console_empty":        "Консоль пуста.",
        "table_empty":          "Таблица Systems пуста.",

        # --- Меню экспорта ---
        "export_console":       "📄  Консоль → .txt",
        "export_systems":       "📊  Системы → .csv",
        "export_console_title": "Сохранить консоль как",
        "export_systems_title": "Сохранить таблицу как",
        "export_filter_txt":    "Текстовые файлы (*.txt)",
        "export_filter_csv":    "CSV файлы (*.csv)",
        "export_done_title":    "Экспорт завершён",
        "export_done_text":     "Файл сохранён:\n{path}",
        "export_open_folder":   "Открыть папку",
        "export_error":         "Ошибка экспорта",
        "export_write_failed":  "Не удалось записать файл:\n{e}",
        "export_nothing_title": "Нечего экспортировать",

        # --- Context menu Systems ---
        "ctx_open_log":         "📁  Открыть папку с логом",
        "ctx_open_excel":       "📊  Открыть папку с Excel-отчётом",
        "ctx_copy_name":        "📋  Копировать имя системы",
        "ctx_copy_serial":      "📋  Копировать серийный номер",
        "ctx_copied":           "Скопировано: {text}",

        # --- Ошибки ---
        "err_folder_gone":      "Папка больше не существует!",
        "err_no_result":        "Результат ещё не готов!",
        "err_open_folder":      "Не удалось открыть папку:\n{e}",
        "err_open_readme":      "Не удалось открыть README: {e}",
        "err_open_changelog":   "Не удалось открыть CHANGELOG: {e}",
        "err_readme_missing":   "README.txt не найден рядом со скриптом:\n{path}",
        "err_changelog_missing":"CHANGELOG.txt не найден рядом со скриптом:\n{path}",
        "err_url":              "Не удалось открыть URL:\n{e}",
        "err_critical":         "Произошла ошибка",
        "err_selftest":         "Ошибка Self-test",
        "err_drop_unsupported": "Поддерживаются только .txt файлы и папки.",

        # --- Окно Settings ---
        "settings_title":       "Настройки",
        "settings_general":     "Общие",
        "settings_output":      "Вывод",
        "settings_diagnostics": "Диагностика",
        "settings_start_mode":  "Режим запуска:",
        "settings_rb_single":   "Один файл",
        "settings_rb_batch":    "Папка (пакетно)",
        "settings_rb_last":     "Последний использованный",
        "settings_default_folder":        "Папка по умолчанию для диалогов открытия:",
        "settings_default_folder_ph":     "(пусто = последняя открытая папка)",
        "settings_export_folder":         "Папка по умолчанию для экспорта:",
        "settings_always_ask_export":     "Всегда спрашивать место экспорта",
        "settings_auto_open":             "Автоматически открывать Excel после создания",
        "settings_include_synthetic":     "Добавлять синтетические строки (Memory / System Disk Drive)",
        "settings_clear_console":         "Очищать консоль при новом запуске",
        "settings_clear_table":           "Очищать таблицу Systems при новом запуске",
        "settings_verbose":               "Подробный лог",
        "settings_language":              "Язык:",
        "settings_reset":                 "Сбросить настройки",
        "settings_reset_title":           "Сброс настроек",
        "settings_reset_text":            "Сбросить все настройки на значения по умолчанию?\n\nНичего не сохранится, пока вы не нажмёте Сохранить.",
        "settings_select_default_folder": "Выберите папку по умолчанию",
        "settings_select_export_folder":  "Выберите папку для экспорта",
        "settings_restart_title":         "Язык изменён",
        "settings_restart_text":          "Язык интерфейса изменится после перезапуска приложения.\n\nПерезапустить сейчас?",

        # --- Окно Customer / Project ---
        "cust_dialog_title":    "Заказчик и Проект",
        "cust_dialog_header":   "Введите данные Заказчика и Проекта",
        "cust_dialog_hint":     "Эти значения будут записаны в колонки B и C\nво все строки Excel-отчёта.",
        "cust_label_customer":  "Заказчик в CRM2:",
        "cust_label_project":   "Проект CRM2:",
        "cust_ph_customer":     "например, ПАО Ростелеком",
        "cust_ph_project":      "например, ЦОД-МСК-2026",
        "cust_continue":        "Продолжить",
        "settings_ask_customer": "Запрашивать Заказчика / Проект перед запуском",

        # --- Окно «Детальный анализ оборудования» ---
        "detailed_analysis_title":       "Детальный анализ оборудования",
        "detailed_analysis_placeholder": "Раздел в разработке. Здесь будет отображаться детальная информация по оборудованию.",
        "analysis_no_source":            "Файл или папка не выбраны",
        "analysis_folder":               "папка",
        "analysis_file":                 "файл",

        # --- Окно Self-test ---
        "selftest_title":       "Self-test",
        "selftest_result":      "Результат: {ok} OK, {fail} FAIL",
        "selftest_copy":        "📋 Копировать в буфер",
        "selftest_status":      "Self-test: {ok} OK, {fail} FAIL",

        # --- About ---
        "about_title":          "О программе",
        "about_text": (
            "<h3>{name}</h3>"
            "<p><b>Версия:</b> {version}</p>"
            "<p>Парсер логов Huawei Storage (V6, V5, V3).<br>"
            "Формирует Excel-отчёты по форме ЗИП.</p>"
            "<hr>"
            "<p><b>Разработчик:</b> Баринштейн Даниил<br>"
            "<b>Контакт:</b> Tg: @Tz1n4</p>"
            "<hr>"
            "<p>© 2026</p>"
        ),

        # --- Quick Start ---
        "qs_title":             "Быстрый старт",
        "qs_header":            "{name} — Быстрый старт",
        "qs_step1":             "<b>1. Выберите режим</b>",
        "qs_single_desc":       "<b>Один файл</b> — разобрать один .txt лог",
        "qs_batch_desc":        "<b>Папка (пакетно)</b> — разобрать все .txt логи в папке и объединить в один Excel-отчёт",
        "qs_step2":             "<b>2. Выберите путь</b> — нажмите Обзор или перетащите файл/папку.",
        "qs_step3":             "<b>3. Нажмите Запустить</b> — Excel-отчёт (форма ЗИП) будет создан рядом с логом (или в папке в пакетном режиме).",
        "qs_step4":             "<b>4. Открыть папку с результатом</b> — перейти к месту сохранения отчёта.",
        "qs_supported":         "<b>Поддерживаемые системы:</b>",
        "qs_troubleshooting":   "<b>Решение проблем:</b> если у компонента написано <i>\"Описание отсутствует, требуется проверка в Spare Query\"</i>, значит блок Elabel для этого компонента пуст в логе — проверьте вручную в Spare Query.",
        "qs_footer":            "<b>F5</b> — Self-test, <b>F1</b> — снова открыть это окно.",

        # --- CLI ---
        "cli_usage_title":      "Использование:",
        "cli_usage_gui":        "  python Main.py                       → запуск GUI",
        "cli_usage_single":     "  python Main.py log.txt               → один файл",
        "cli_usage_batch":      "  python Main.py C:\\Logs               → все .txt в папке",
        "cli_usage_batch_force":"  python Main.py --batch C:\\Logs       → принудительный пакетный режим",
        "cli_usage_options_title": "Опции:",
        "cli_usage_customer":   '  --customer "Название"                → Заказчик в CRM2 (колонка B)',
        "cli_usage_project":    '  --project "Название"                 → Проект CRM2 (колонка C)',
        "cli_customer":         "Заказчик:   {customer}",
        "cli_project":          "Проект:     {project}",
        "cli_err_missing_value":"Ошибка: {flag} требует значение.",
        "cli_special_title":    "Специальные команды:",
        "cli_help":             "  python Main.py --help, -h            → эта справка",
        "cli_readme":           "  python Main.py --readme              → открыть README.txt",
        "cli_selftest":         "  python Main.py --selftest            → Self-test в консоли",
        "cli_changelog":        "  python Main.py --changelog           → открыть CHANGELOG.txt",
        "cli_err_no_path":      "Ошибка: путь не указан.",
        "cli_err_path_not_found":"Ошибка: путь не найден: {path}",
        "cli_err_batch_needs_dir":"Ошибка: --batch требует папку, получен файл: {path}",
        "cli_err_not_folder":   "Ошибка: не папка: {path}",
        "cli_err_no_txt":       "Ошибка: .txt файлы не найдены в {path}",
        "cli_warn_not_txt":     "Предупреждение: файл не похож на .txt: {path}",
        "cli_warn_unexpected":  "Предупреждение: лишний аргумент проигнорирован: {arg}",
        "cli_reading_file":     "Чтение файла: {path}",
        "cli_system":           "Система:    {name}",
        "cli_model":            "Модель:     {model}",
        "cli_serial":           "Серийник:   {serial}",
        "cli_version":          "Версия:     {version}",
        "cli_components":       "Компоненты: {n}",
        "cli_generating":       "Генерация Excel...",
        "cli_excel_created":    "Excel создан: {path}",
        "cli_found_files":      "Найдено {n} .txt файл(ов) в папке",
        "cli_processing":       ">>> Обработка [{idx}/{total}]: {name}",
        "cli_ok":               "    OK: {name} ({n} компонентов)",
        "cli_skip":             "    ПРОПУСК: {e}",
        "cli_no_success":       "Ошибка: ни один лог не разобран успешно ({n} ошибок).",
        "cli_generating_batch": "Генерация общего Excel...",
        "cli_parsed_summary":   "Разобрано: {ok}/{total}",
        "cli_errors_suffix":    ", ошибок: {n}",
        "cli_selftest_header":  "SELF-TEST",
        "cli_selftest_result":  "Результат: {ok} OK, {fail} FAIL",
        "cli_selftest_module_missing":"Ошибка: модуль Utils_SelfTest не найден.",
        "cli_opened":           "Открыто: {path}",
        "cli_err_open":         "Ошибка: не удалось открыть {what}: {e}",
    },
}


# ==============================================================================
# API
# ==============================================================================

def tr(key: str) -> str:
    """Простой перевод без подстановок."""
    lang_dict = STRINGS.get(_current_lang, STRINGS[DEFAULT_LANGUAGE])
    if key in lang_dict:
        return lang_dict[key]
    return STRINGS[DEFAULT_LANGUAGE].get(key, key)


def trf(key: str, **kwargs) -> str:
    """Перевод с подстановкой именованных аргументов через .format()."""
    template = tr(key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template