#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils_SelfTest.py — self-test для HuaHW-Tracker.
"""

import os
import sys


def run_checks(test_file=None):
    results = []

    def add(group, label, ok, extra="", subgroup=""):
        results.append({
            "group": group, 
            "subgroup": subgroup,
            "label": label, 
            "ok": bool(ok), 
            "extra": extra
        })

    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # --------------------------------------------------------------------------
    # PYTHON И ЗАВИСИМОСТИ
    # --------------------------------------------------------------------------
    add("Python", "Python interpreter", True, f"v{sys.version.split()[0]}")
    
    try:
        from PyQt6.QtCore import QT_VERSION_STR
        add("Python", "PyQt6 (Qt)", True, f"Qt {QT_VERSION_STR}")
    except ImportError as e:
        add("Python", "PyQt6 (Qt)", False, str(e))

    try:
        import openpyxl
        add("Python", "openpyxl", True, f"v{openpyxl.__version__}")
    except ImportError as e:
        add("Python", "openpyxl", False, str(e))

    # --------------------------------------------------------------------------
    # ФАЙЛЫ ПРОЕКТА (HW-Tracker Files)
    # --------------------------------------------------------------------------
    add("HW-Tracker Files", "Script folder in sys.path", script_dir in sys.path, script_dir)
    
    files_structure = {
        "Core": {
            "Core/Core_Base_Parser.py": "Core_Base_Parser",
            "Core/Core_Export_Excel.py": "Core_Export_Excel",
            "Core/Core_Export_Excel_Details.py": "Core_Export_Excel_Details",
            "Core/Core_System_Info.py": "Core_System_Info",
            "Core/Core_CRM_Checker.py": "Core_CRM_Checker",
        },
        "GUI": {
            "GUI/Gui_App.py": "Gui_App",
            "GUI/Gui_Main.py": "Gui_Main",
            "GUI/Gui_Settings.py": "Gui_Settings",
            "GUI/Gui_Workers.py": "Gui_Workers",
            "GUI/Gui_SelfTest.py": "Gui_SelfTest",
            "GUI/Gui_Styles.py": "Gui_Styles",
        },
        "GUI_Dialogs": {
            "GUI/Gui_Dialogs/Gui_Dialog_Detailed_Analysis.py": "Gui_Dialog_Detailed_Analysis",
            "GUI/Gui_Dialogs/Gui_Dialog_Customer.py": "Gui_Dialog_Customer",
        },
        "GUI_Details_Tabs": {
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_Base_Tab.py": "Gui_Details_Base_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_BBU_Tab.py": "Gui_Details_BBU_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_Controller_Tab.py": "Gui_Details_Controller_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_DAE_Tab.py": "Gui_Details_DAE_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_Disk_Drive_Tab.py": "Gui_Details_Disk_Drive_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_DSW_Tab.py": "Gui_Details_DSW_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_Exp_Module_Tab.py": "Gui_Details_Exp_Module_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_Fan_Tab.py": "Gui_Details_Fan_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_IO_Tab.py": "Gui_Details_IO_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_PSU_Tab.py": "Gui_Details_PSU_Tab",
            "GUI/Gui_Dialogs/Gui_Details_Tabs/Gui_Details_SFP_Tab.py": "Gui_Details_SFP_Tab",
        },
        "Parsers": {
            "Parsers/Parser_V3.py": "Parser_V3",
            "Parsers/Parser_V5.py": "Parser_V5",
            "Parsers/Parser_V6.py": "Parser_V6",
        },
        "Parsers_Details": {
            "Parsers/Parsers_Details/Parser_BBU_Details.py": "Parser_BBU_Details",
            "Parsers/Parsers_Details/Parser_Controller_Details.py": "Parser_Controller_Details",
            "Parsers/Parsers_Details/Parser_DAE_Details.py": "Parser_DAE_Details",
            "Parsers/Parsers_Details/Parser_Disk_Drive_Details.py": "Parser_Disk_Drive_Details",
            "Parsers/Parsers_Details/Parser_DSW_Details.py": "Parser_DSW_Details",
            "Parsers/Parsers_Details/Parser_Exp_Module_Details.py": "Parser_Exp_Module_Details",
            "Parsers/Parsers_Details/Parser_Fan_Details.py": "Parser_Fan_Details",
            "Parsers/Parsers_Details/Parser_IO_Details.py": "Parser_IO_Details",
            "Parsers/Parsers_Details/Parser_PSU_Details.py": "Parser_PSU_Details",
            "Parsers/Parsers_Details/Parser_SFP_Details.py": "Parser_SFP_Details",
        },
        "Utils": {
            "Utils/Utils_Constants.py": "Utils_Constants",
            "Utils/Utils_Locale.py": "Utils_Locale",
            "Utils/Utils_Regex_Helpers.py": "Utils_Regex_Helpers",
            "Utils/Utils_SelfTest.py": "Utils_SelfTest",
            "Utils/Utils_System.py": "Utils_System",
            "Utils/Utils_Settings.py": "Utils_Settings",
        }
    }

    for subgroup, files in files_structure.items():
        for path, name in files.items():
            exists = os.path.exists(os.path.join(script_dir, path))
            add("HW-Tracker Files", name, exists, subgroup=subgroup)

    # --------------------------------------------------------------------------
    # ШАБЛОНЫ EXCEL (Templates Files)
    # --------------------------------------------------------------------------
    template_zip = os.path.join(script_dir, "Core", "Core_Form.xlsx")
    add("Templates Files", "Template Core_Form.xlsx", os.path.exists(template_zip), 
        template_zip if os.path.exists(template_zip) else "NOT FOUND")

    template_details = os.path.join(script_dir, "Core", "Core_Form_Details.xlsx")
    add("Templates Files", "Template Core_Form_Details.xlsx", os.path.exists(template_details), 
        template_details if os.path.exists(template_details) else "NOT FOUND")

    return results