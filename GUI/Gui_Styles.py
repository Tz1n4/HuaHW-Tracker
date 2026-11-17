#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gui_Styles.py — общие QSS-стили для интерфейса.
"""

STYLE_BTN_ACTIVE = """
    QPushButton {
        background-color: #2196F3;
        color: #FFFFFF;
        border: 1px solid #2196F3;
        border-radius: 5px;
        padding: 10px;
        font-weight: bold;
    }
"""

STYLE_BTN_INACTIVE = """
    QPushButton {
        background-color: #2d2d2d;
        color: #cccccc;
        border: 1px solid #555;
        border-radius: 5px;
        padding: 10px;
    }
    QPushButton:hover { background-color: #3d3d3d; }
"""

STYLE_BTN_DARK = """
    QPushButton {
        background-color: #2d2d2d;
        color: #d4d4d4;
        border: 1px solid #555555;
        border-radius: 5px;
        padding: 10px;
    }
    QPushButton:hover { background-color: #3d3d3d; }
    QPushButton:disabled {
        background-color: #1e1e1e;
        color: #666666;
        border: 1px solid #333333;
    }
"""

STYLE_BTN_DANGER = """
    QPushButton {
        background-color: #b71c1c;
        color: #ffffff;
        border: 1px solid #b71c1c;
        border-radius: 5px;
        padding: 10px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #d32f2f; }
    QPushButton:disabled {
        background-color: #5a1f1f;
        color: #999999;
        border: 1px solid #3a1414;
    }
"""