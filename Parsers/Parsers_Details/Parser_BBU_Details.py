#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser_BBU_Details.py — детальный разбор BBU для всех версий.
"""

import re
from datetime import datetime, timedelta


def _calculate_dates(delivered_on):
    """Вычисляет остаток и возраст на основе даты поставки."""
    real_remain_days = "N/A"
    end_of_life_date = "N/A"
    age_days = "N/A"
    
    if delivered_on and delivered_on != "N/A":
        try:
            parts = delivered_on.replace('/', '-').split('-')
            if len(parts) == 3:
                year, month, day = map(int, parts)
                dt_delivered = datetime(year, month, day)
                
                dt_eol = dt_delivered + timedelta(days=2920) # 8 лет
                end_of_life_date = dt_eol.strftime("%Y-%m-%d")
                
                today = datetime.now()
                real_remain_days = (dt_eol - today).days
                age_days = (today - dt_delivered).days
        except Exception:
            pass
            
    return real_remain_days, age_days, end_of_life_date


def parse_bbu_details(content, sys_version="V3"):
    """Парсит BBU и возвращает список словарей (V3/V5/V6)."""
    bbu_list = []

    # V6 / 2600 V5 (Секция BBU Info)
    bbu_section_match = re.search(r'BBU Info-+\n(.*?)(?=\n\s*[A-Z][A-Za-z ]+-{5,}|\Z)', content, re.DOTALL)
    if bbu_section_match:
        section_text = bbu_section_match.group(1)
        
        # ИСПРАВЛЕНИЕ: (?:^|\n) чтобы ловить самый первый ID в секции
        blocks = re.split(r'(?:^|\n)\s*(?:BBU ID:|ID:)\s*', section_text)
        
        for block in blocks[1:]:
            # Восстанавливаем префикс для регулярки ID
            bbu_id_match = re.match(r'(\S+)', block)
            if not bbu_id_match:
                continue
            bbu_id = bbu_id_match.group(1)
            
            def get_val(pattern, default="N/A"):
                m = re.search(pattern, block)
                return m.group(1).strip() if m else default

            delivered_on = get_val(r'Delivered On:\s*(.+)')
            real_remain_days, age_days, end_of_life_date = _calculate_dates(delivered_on)
            
            voltage = get_val(r'(?:Current Voltage|Voltage)(?:\(V\)|\(0\.1V\))?:\s*(.+)')
            remain_life = get_val(r'(?:RemainLife|Remaining Lifetime)(?:\(days\))?:\s*(\d+|--)')
            discharge_times = get_val(r'(?:Discharge Times|Number Of Discharges):\s*(.+)')

            bbu_list.append({
                "id": bbu_id,
                "health": get_val(r'Health Status:\s*(.+)'),
                "running": get_val(r'Running Status:\s*(.+)'),
                "voltage": voltage,
                "discharge_times": discharge_times,
                "firmware": get_val(r'Firmware Version:\s*(.+)'),
                "delivered_on": delivered_on,
                "charge_state": get_val(r'Charge State:\s*(.+)'),
                "remain_life_log": remain_life,
                "real_remain_days": real_remain_days,
                "age_days": age_days,
                "end_of_life": end_of_life_date,
                "item": get_val(r'Item=(\S+)'),
                "barcode": get_val(r'BarCode=(\S+)'),
                "desc": get_val(r'Description=(.+)'),
                "manufactured": get_val(r'Manufactured=(\S+)'),
            })
            
        return bbu_list

    # Фоллбэк для остальных V6/V5
    pattern_v6 = r'BBU\(([^)]+)\)-+\n(.*?)(?=\s*BBU\([^)]+\)|\Z)'
    for m in re.finditer(pattern_v6, content, re.DOTALL):
        block = m.group(2)
        
        def get_val_v6(pattern, default="N/A"):
            match = re.search(pattern, block)
            return match.group(1).strip() if match else default
            
        delivered_on = get_val_v6(r'Delivered On:\s*(.+)')
        real_remain_days, age_days, end_of_life_date = _calculate_dates(delivered_on)
        
        bbu_list.append({
            "id": m.group(1),
            "health": get_val_v6(r'Health Status:\s*(.+)'),
            "running": get_val_v6(r'Running Status:\s*(.+)'),
            "voltage": get_val_v6(r'(?:Current Voltage|Voltage)(?:\(V\)|\(0\.1V\))?:\s*(.+)'),
            "discharge_times": get_val_v6(r'(?:Discharge Times|Number Of Discharges):\s*(.+)'),
            "firmware": get_val_v6(r'Firmware Version:\s*(.+)'),
            "delivered_on": delivered_on,
            "charge_state": get_val_v6(r'Charge State:\s*(.+)'),
            "remain_life_log": get_val_v6(r'(?:RemainLife|Remaining Lifetime)(?:\(days\))?:\s*(\d+|--)'),
            "real_remain_days": real_remain_days,
            "age_days": age_days,
            "end_of_life": end_of_life_date,
            "item": get_val_v6(r'Item=(\S+)'),
            "barcode": get_val_v6(r'BarCode=(\S+)'),
            "desc": get_val_v6(r'Description=(.+)'),
            "manufactured": get_val_v6(r'Manufactured=(\S+)'),
        })
        
    return bbu_list