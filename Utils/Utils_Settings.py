#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils_Settings.py — работа с файлом Settings.ini в обход багов QSettings.
"""

import os

_SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Settings.ini"
)


def read_mode():
    try:
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("mode="):
                        return line.split("=", 1)[1].strip() or "single"
    except Exception:
        pass
    return "single"


def write_mode(is_batch):
    mode_value = "batch" if is_batch else "single"
    try:
        lines = []
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith("mode="):
                lines[i] = f"mode={mode_value}\n"
                found = True
                break

        if not found:
            insert_at = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("["):
                    insert_at = i + 1
                    break
            lines.insert(insert_at, f"mode={mode_value}\n")

        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"Failed to write mode to ini: {e}")


def read_components():
    try:
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("detailed_components="):
                        val = line.split("=", 1)[1].strip()
                        val = val.replace('"', '').replace("'", "")
                        if val:
                            return [item.strip() for item in val.split(",")]
    except Exception:
        pass
    return ["Controller", "Disk", "Power Supply", "BBU", "Fan", 
            "I/O Module", "Expansion Board", "SFP Module", "Enclosure"]


def write_components(components):
    components_str = ",".join(components)
    try:
        lines = []
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith("detailed_components="):
                lines[i] = f"detailed_components={components_str}\n"
                found = True
                break

        if not found:
            insert_at = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("["):
                    insert_at = i + 1
                    break
            lines.insert(insert_at, f"detailed_components={components_str}\n")

        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"Failed to write components to ini: {e}")