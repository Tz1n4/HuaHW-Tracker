#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser_Controller_Details.py — детальный разбор контроллеров (V3, V5, V6).
"""

import re


def parse_controller_details(content, sys_version="V3"):
    """Парсит контроллеры и возвращает список словарей."""
    controllers = []

    if sys_version == "V6":
        pattern = r'Control Board\(([^)]+)\)-+\n(.*?)(?=\n\s*Control Board\(|\n\s*Power\(|\n\s*Fan\(|\Z)'
        matches = re.finditer(pattern, content, re.DOTALL)
        for m in matches:
            ctrl_id = m.group(1).strip()
            block = m.group(2)
            parsed = _parse_single_block(block, ctrl_id)
            if parsed:
                controllers.append(parsed)

    elif sys_version in ("V5", "V3"):
        # Ищем секцию Control Board Info (характерно для 2600 V5)
        cb_section = re.search(r'Control Board Info-+\n(.*?)(?=\n\s*[A-Z][A-Za-z ]+-{5,}|\Z)', content, re.DOTALL)
        
        if cb_section:
            section_text = cb_section.group(1)
            # ИСПРАВЛЕНИЕ: (?:^|\n) чтобы ловить самый первый Controller в секции
            id_matches = list(re.finditer(r'(?:^|\n)\s*Controller:\s*([0-9A-Z]{2})\s*\n', section_text))
            for i, m in enumerate(id_matches):
                ctrl_id = m.group(1).strip()
                start_pos = m.start()
                end_pos = id_matches[i + 1].start() if i + 1 < len(id_matches) else len(section_text)
                
                raw_block = section_text[start_pos:end_pos]
                parsed = _parse_single_block(raw_block, ctrl_id)
                if parsed:
                    controllers.append(parsed)
        else:
            # Стандартный поиск для 5110/5500 V5
            id_matches = list(re.finditer(r'(?:^|\n)\s*Controller ID:\s*([0-9A-Z]{2})\s*\n', content))
            for i, m in enumerate(id_matches):
                ctrl_id = m.group(1).strip()
                start_pos = m.start()
                end_pos = id_matches[i + 1].start() if i + 1 < len(id_matches) else len(content)
                
                raw_block = content[start_pos:end_pos]
                
                cut_markers = [r'Management Ethernet port', r'Electronic Sale Label', r'Interface Board', r'FC Port', r'ETH Port', r'SAS Port']
                block = raw_block
                for marker in cut_markers:
                    marker_match = re.search(marker, block)
                    if marker_match:
                        block = block[:marker_match.start()]
                        break
                
                if "Location:" not in block or "Role:" not in block:
                    continue
                    
                parsed = _parse_single_block(block, ctrl_id)
                if parsed:
                    controllers.append(parsed)

    return controllers


def _parse_single_block(block, ctrl_id):
    """Парсит один блок контроллера."""

    def get_val(pattern, default="N/A"):
        m = re.search(pattern, block)
        return m.group(1).strip() if m else default

    ctrl_id = re.split(r'[\s\-]', ctrl_id)[0]

    health = get_val(r'Health Status:\s*(.+)')
    running = get_val(r'Running Status:\s*(.+)')

    if health == "N/A" and running == "N/A":
        return None

    barcode = get_val(r'BarCode=(\S+)')
    item = get_val(r'Item=(\S+)')
    desc = get_val(r'Description=(.+)')
    manufactured = get_val(r'Manufactured=(\S+)')

    cache_cap = get_val(r'Cache Capacity:\s*(.+)')
    if cache_cap == "N/A" and desc != "N/A":
        cache_match = re.search(r'(\d+\*\d+[GM]B? Cache|\d+[GM]B? Cache)', desc)
        if cache_match:
            cache_cap = cache_match.group(1)

    cpu = get_val(r'CPU:\s*(.+)')
    model = get_val(r'BoardType=(\S+)')

    return {
        "id": ctrl_id,
        "health": health,
        "running": running,
        "barcode": barcode,
        "item": item,
        "desc": desc,
        "cache_cap": cache_cap,
        "manufactured": manufactured,
        "cpu": cpu,
        "model": model,
    }