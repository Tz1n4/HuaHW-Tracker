#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils_System.py — системные утилиты.

Открытие файлов, папок и URL в системном просмотрщике/браузере
без привязки к Qt — можно вызывать и из CLI-режима.

Все публичные функции возвращают bool:
    True  — действие выполнено,
    False — не удалось (файл не найден, нет просмотрщика и т.п.).
"""

import os
import sys
import subprocess


def is_windows():
    return sys.platform == "win32"


def is_macos():
    return sys.platform == "darwin"


def is_linux():
    return not is_windows() and not is_macos()


def _spawn(args):
    """Запускает системную команду, не блокируя процесс."""
    try:
        subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        return True
    except (OSError, FileNotFoundError):
        return False


def open_in_system(path):
    """Открывает файл или папку в системном просмотрщике."""
    if not path or not os.path.exists(path):
        return False

    if is_windows():
        try:
            os.startfile(path)
            return True
        except OSError:
            return False

    if is_macos():
        return _spawn(["open", path])

    return _spawn(["xdg-open", path])


def open_url(url):
    """Открывает URL в браузере по умолчанию."""
    if not url:
        return False

    if is_windows():
        try:
            os.startfile(url)
            return True
        except OSError:
            return False

    if is_macos():
        return _spawn(["open", url])

    return _spawn(["xdg-open", url])


def reveal_path(path):
    """Открывает папку и, если возможно, выделяет в ней файл."""
    if not path or not os.path.exists(path):
        return False

    if os.path.isdir(path):
        return open_in_system(path)

    parent = os.path.dirname(path)
    if not parent:
        return False

    if is_windows():
        try:
            subprocess.Popen(
                ["explorer", "/select,", os.path.normpath(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
            return True
        except OSError:
            return open_in_system(parent)

    if is_macos():
        return _spawn(["open", "-R", path])

    return open_in_system(parent)