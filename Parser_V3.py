#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser_V3.py — парсер логов Huawei Storage V3.

Поддерживает два подтипа V3:
1. Dorado6000 V3   (Product Model: Dorado6000 V3) — почти как V6.
2. OceanStor V3    (Product Model: 5300 V3, ...) — другая структура.

Каждый компонент — dict:
    {
        "id":   str,   # уникальный ID из лога
        "name": str,   # Description из Elabel (или заглушка)
        "type": str,   # тип компонента
        "bom":  str,   # Item из Elabel (или BOM из SN)
    }
"""

import re

from Utils_Regex_Helpers import (
    extract_label_fields,
    extract_bom_from_serial,
    make_name_from_label,
    make_bom_from_label_or_serial,
)
from Utils_Constants import TEXT_NO_DESCRIPTION


class V3Parser:
    """Парсер логов Huawei Storage V3 (Dorado + OceanStor)."""

    def __init__(self, content, sys_info):
        self.content = content
        self.sys_info = sys_info

    # --------------------------------------------------------------------------
    # ДИСПЕТЧЕР
    # --------------------------------------------------------------------------

    def parse_all(self, progress_callback=None):
        """Определяет подтип V3 и запускает нужный парсер."""
        model = self.sys_info.get("model", "")

        if "Dorado" in model:
            return self._parse_dorado(progress_callback)
        elif "V3" in model:
            return self._parse_oceanstor(progress_callback)
        else:
            raise ValueError(f"Unknown V3 subtype, model: '{model}'")

    # --------------------------------------------------------------------------
    # DORADO6000 V3
    # --------------------------------------------------------------------------

    def _parse_dorado(self, progress_callback=None):
        """Парсит Dorado6000 V3."""

        def _notify(text, percent):
            if progress_callback:
                progress_callback(text, percent)

        components = []

        _notify("Parsing enclosures...", 15)
        components.extend(self.parse_enclosures())

        _notify("Parsing controllers...", 25)
        components.extend(self.parse_controllers())

        _notify("Parsing disks...", 40)
        components.extend(self.parse_disks())

        _notify("Parsing power supplies...", 50)
        components.extend(self.parse_power())

        _notify("Parsing fans...", 60)
        components.extend(self.parse_fan())

        _notify("Parsing BBUs...", 70)
        components.extend(self.parse_bbu())

        _notify("Parsing I/O modules...", 80)
        components.extend(self.parse_iom())

        _notify("Parsing expander boards...", 85)
        components.extend(self.parse_expander())

        _notify("Parsing SFPs...", 95)
        components.extend(self.parse_sfp())

        return components

    # --------------------------------------------------------------------------
    # 1. ENCLOSURES (V3 Dorado)
    # --------------------------------------------------------------------------

    def parse_enclosures(self):
        """Парсит Enclosure Info (Dorado V3)."""
        components = []
        seen_ids = set()

        section_match = re.search(
            r'Enclosure Info-{5,}(.*?)(?=\n[A-Z][A-Za-z ]+-{5,}|\Z)',
            self.content,
            re.DOTALL
        )
        if not section_match:
            return components

        section_text = section_match.group(1)

        pattern = (
            r'\n\s*(?:Enclosure ID|ID):\s*((?:CTE|DAE|DSW)\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*(?:Enclosure ID|ID):|\Z)'
        )

        for m in re.finditer(pattern, section_text, re.DOTALL):
            enc_id = m.group(1)
            if enc_id in seen_ids:
                continue
            seen_ids.add(enc_id)

            block = m.group(2)

            if 'Logic Type:' not in block:
                continue

            sn_m = re.search(r'SN:\s*(\S+)', block)
            sn = sn_m.group(1).strip() if sn_m else None

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=\n\s*(?:Enclosure ID|ID):|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            bom = make_bom_from_label_or_serial(lbl, serial=sn)
            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            if enc_id.startswith("DSW"):
                comp_type = "Data Switch"
            else:
                comp_type = "Enclosure"

            components.append({
                "id": enc_id,
                "name": name,
                "type": comp_type,
                "bom": bom,
            })

        return components

    # --------------------------------------------------------------------------
    # 2. CONTROLLERS (V3 Dorado)
    # --------------------------------------------------------------------------

    def parse_controllers(self):
        """Парсит контроллеры (0A, 0B, 1A, 1B)."""
        components = []
        seen_ids = set()

        pattern = (
            r'Controller ID:\s*(\d+[A-Z])\s*\n'
            r'(.*?)'
            r'(?=\n\s*Controller ID:|\n[A-Z][A-Za-z ]+[-]{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            ctrl_id = m.group(1)
            if ctrl_id in seen_ids:
                continue
            seen_ids.add(ctrl_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Controller ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A" and lbl["barcode"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   ctrl_id,
                "name": name,
                "type": "Controller",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 3. DISKS (V3 Dorado — таблица "Disk Info" идентична V6)
    # --------------------------------------------------------------------------

    def parse_disks(self):
        """Парсит диски из таблицы Disk Info + Elabel."""
        components = []
        seen_ids = set()

        table_match = re.search(
            r'#{3,}\s*Disk Info\s*#{3,}(.*?)#{3,}',
            self.content,
            re.DOTALL
        )
        if not table_match:
            return components

        table_content = table_match.group(1)

        row_pattern = (
            r'((?:CTE|DAE)\d+\.\d+)\s+'
            r'.+?\s+'
            r'(?:Online|Offline)\s+'
            r'(\S+)\s+'
            r'[\d.]+TB\s+'
            r'Member Disk\s+'
            r'\d+\s+'
            r'\S+\s+\S+\s+'
            r'(\S{10,})\s+'
            r'(\S+)'
        )

        for m in re.finditer(row_pattern, table_content):
            disk_id = m.group(1)
            disk_type = m.group(2)
            barcode = m.group(3)
            item = m.group(4)

            if disk_id in seen_ids:
                continue
            seen_ids.add(disk_id)

            desc = "N/A"

            detail_match = re.search(
                rf'Disk Frame and Slot ID:\s*{re.escape(disk_id)}\s*\n(.*?)(?=\n\s*Disk ID:|\Z)',
                self.content,
                re.DOTALL
            )
            if detail_match:
                detail_block = detail_match.group(1)
                elabel_m = re.search(
                    r'Disk Elabel:\s*(.*?)(?=\n\s*Disk [A-Z]|\Z)',
                    detail_block,
                    re.DOTALL
                )
                if elabel_m:
                    lbl = extract_label_fields(elabel_m.group(1))
                    if lbl["description"] != "N/A":
                        desc = lbl["description"]
                    if lbl["item"] != "N/A":
                        item = lbl["item"]

            name = desc if desc != "N/A" else disk_type

            components.append({
                "id":   disk_id,
                "name": name,
                "type": "Disk",
                "bom":  item,
            })

        return components

    # --------------------------------------------------------------------------
    # 4. POWER SUPPLY (V3 Dorado)
    # --------------------------------------------------------------------------

    def parse_power(self):
        """Парсит блоки Power Info (Power ID: CTE0.PSU0)."""
        components = []
        seen_ids = set()

        pattern = (
            r'Power ID:\s*([A-Z]+\d+\.(?:PSU|POWER)\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*Power ID:|\n[A-Za-z][A-Za-z ]*-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            psu_id = m.group(1)
            if psu_id in seen_ids:
                continue
            seen_ids.add(psu_id)

            block = m.group(2)

            sn_m = re.search(r'Serial Number:\s*(\S+)', block)
            sn = sn_m.group(1).strip() if sn_m else None

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Power ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                item_m = re.search(r'Item:\s*(\S+)', block)
                if item_m:
                    lbl["item"] = item_m.group(1).strip()

            bom = make_bom_from_label_or_serial(lbl, serial=sn)

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   psu_id,
                "name": name,
                "type": "Power Supply",
                "bom":  bom,
            })

        return components

    # --------------------------------------------------------------------------
    # 5. FAN (V3 Dorado)
    # --------------------------------------------------------------------------

    def parse_fan(self):
        """Парсит блоки Fan Info (Fan ID: CTE0.A.FAN0)."""
        components = []
        seen_ids = set()
        
        pattern = (
            r'Fan ID:\s*([A-Z]+\d+(?:\.[A-Z])?\.(?:FAN|PSU)\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*Fan ID:|\n[A-Za-z][A-Za-z ]*-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            fan_id = m.group(1)
            if fan_id in seen_ids:
                continue
            seen_ids.add(fan_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Fan ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   fan_id,
                "name": name,
                "type": "Fan",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 6. BBU (V3 Dorado)
    # --------------------------------------------------------------------------

    def parse_bbu(self):
        """Парсит блоки BBU Info (BBU ID: CTE0.0)."""
        components = []
        seen_ids = set()

        pattern = (
            r'BBU ID:\s*([A-Z]+\d+\.\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*BBU ID:|\n[A-Za-z][A-Za-z ]*-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            bbu_id = m.group(1)
            if bbu_id in seen_ids:
                continue
            seen_ids.add(bbu_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=BBU ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   bbu_id,
                "name": name,
                "type": "BBU",
                "bom":  lbl["item"],
            })

        return components
        
    # --------------------------------------------------------------------------
    # 7. I/O MODULE (V3 Dorado)
    # --------------------------------------------------------------------------

    def parse_iom(self):
        """Парсит Interface Board (IOM + SMM)."""
        components = []
        seen_ids = set()

        section_match = re.search(
            r'Interface Board-{5,}(.*?)(?=\n[A-Z][A-Za-z ]+-{5,}|\Z)',
            self.content,
            re.DOTALL
        )
        if not section_match:
            return components

        section_text = section_match.group(1)

        pattern = (
            r'Board ID:\s*(\S+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*Board ID:|\Z)'
        )

        for m in re.finditer(pattern, section_text, re.DOTALL):
            board_id = m.group(1)
            if board_id in seen_ids:
                continue
            seen_ids.add(board_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Board ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   board_id,
                "name": name,
                "type": "I/O Module",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 8. EXPANDER BOARD (V3 Dorado)
    # --------------------------------------------------------------------------

    def parse_expander(self):
        """Парсит Expander Board Info (Board ID: DAE000.A)."""
        components = []
        seen_ids = set()

        section_match = re.search(
            r'Expander Board Info-{5,}(.*?)(?=\n[A-Z][A-Za-z ]+-{5,}|\Z)',
            self.content,
            re.DOTALL
        )
        if not section_match:
            return components

        section_text = section_match.group(1)

        pattern = (
            r'Board ID:\s*(\S+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*Board ID:|\Z)'
        )

        for m in re.finditer(pattern, section_text, re.DOTALL):
            exp_id = m.group(1)
            if exp_id in seen_ids:
                continue
            seen_ids.add(exp_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Board ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   exp_id,
                "name": name,
                "type": "Expansion Board",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 9. SFP MODULE (V3 Dorado)
    # --------------------------------------------------------------------------

    def parse_sfp(self):
        """Парсит SFP-модули из секции FC Port."""
        components = []
        seen_serials = set()

        pattern = (
            r'sfp info:\s*\n'
            r'\s*sfp:\s*(\S+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*(?:ID:|sfp info:)|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            sfp_id = m.group(1)
            block = m.group(2)

            vendor_m = re.search(r'Vendor:\s*(.+)', block)
            model_m = re.search(r'Model:\s*(.+)', block)
            sn_m = re.search(r'SN:\s*(\S+)', block)

            vendor = vendor_m.group(1).strip() if vendor_m else ""
            model = model_m.group(1).strip() if model_m else ""
            sn = sn_m.group(1).strip() if sn_m else ""

            if not vendor and not model:
                continue

            if sn and sn in seen_serials:
                continue
            if sn:
                seen_serials.add(sn)

            sfp_name = f"{vendor} {model}".strip()

            components.append({
                "id":   sfp_id,
                "name": sfp_name,
                "type": "SFP Module",
                "bom":  sfp_name,
            })

        return components
        
    # --------------------------------------------------------------------------
    # OCEANSTOR V3
    # --------------------------------------------------------------------------

    def _parse_oceanstor(self, progress_callback=None):
        """Парсит OceanStor 5300 V3."""

        def _notify(text, percent):
            if progress_callback:
                progress_callback(text, percent)

        components = []

        _notify("Parsing enclosures...", 15)
        components.extend(self.parse_enclosures_oceanstor())

        _notify("Parsing controllers...", 25)
        components.extend(self.parse_controllers_oceanstor())

        _notify("Parsing disks...", 40)
        components.extend(self.parse_disks_oceanstor())

        _notify("Parsing power supplies...", 50)
        components.extend(self.parse_power_oceanstor())

        _notify("Parsing fans...", 60)
        components.extend(self.parse_fan_oceanstor())

        _notify("Parsing BBUs...", 70)
        components.extend(self.parse_bbu_oceanstor())

        _notify("Parsing I/O modules...", 80)
        components.extend(self.parse_iom_oceanstor())

        _notify("Parsing expander boards...", 85)
        components.extend(self.parse_expander_oceanstor())

        _notify("Parsing SFPs...", 95)
        components.extend(self.parse_sfp_oceanstor())

        return components

    # --------------------------------------------------------------------------
    # OCEANSTOR: ENCLOSURES (без Elabel!)
    # --------------------------------------------------------------------------

    def parse_enclosures_oceanstor(self):
        """Парсит Enclosure Info для OceanStor V3 (без Elabel)."""
        components = []
        seen_ids = set()

        section_match = re.search(
            r'ENCLOSURE-{5,}(.*?)(?=\n[A-Z][A-Za-z ]+-{5,}|\Z)',
            self.content,
            re.DOTALL
        )
        if not section_match:
            return components

        section_text = section_match.group(1)

        pattern = (
            r'\n\s*(?:Enclosure ID|ID):\s*((?:CTE|DAE|DSW)\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*(?:Enclosure ID|ID):|\Z)'
        )
        
        for m in re.finditer(pattern, section_text, re.DOTALL):
            enc_id = m.group(1)
            if enc_id in seen_ids:
                continue
            seen_ids.add(enc_id)

            block = m.group(2)

            sn_m = re.search(r'SN:\s*(\S+)', block)
            sn = sn_m.group(1).strip() if sn_m else None

            bom = extract_bom_from_serial(sn)

            name = TEXT_NO_DESCRIPTION

            if enc_id.startswith("DSW"):
                comp_type = "Data Switch"
            else:
                comp_type = "Enclosure"

            components.append({
                "id":   enc_id,
                "name": name,
                "type": comp_type,
                "bom":  bom,
            })

        return components

    # --------------------------------------------------------------------------
    # OCEANSTOR: CONTROLLERS (с Elabel!)
    # --------------------------------------------------------------------------

    def parse_controllers_oceanstor(self):
        """Парсит контроллеры OceanStor V3 (0A, 0B)."""
        components = []
        seen_ids = set()

        pattern = (
            r'Controller ID:\s*(\d+[A-Z])\s*\n'
            r'(.*?)'
            r'(?=\n+\s*Controller ID:|\n+[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            ctrl_id = m.group(1)
            if ctrl_id in seen_ids:
                continue
            seen_ids.add(ctrl_id)

            block = m.group(2)

            if "Electronic Label:" not in block:
                continue

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Controller ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A" and lbl["barcode"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   ctrl_id,
                "name": name,
                "type": "Controller",
                "bom":  lbl["item"],
            })

        return components
        
    # --------------------------------------------------------------------------
    # OCEANSTOR: DISKS (таблица Disk Info — идентична V6)
    # --------------------------------------------------------------------------

    def parse_disks_oceanstor(self):
        """Парсит диски OceanStor V3 (таблица Disk Info + Elabel)."""
        components = []
        seen_ids = set()

        table_match = re.search(
            r'#{3,}\s*Disk Info\s*#{3,}(.*?)#{3,}',
            self.content,
            re.DOTALL
        )
        if not table_match:
            return components

        table_content = table_match.group(1)

        row_pattern = (
            r'((?:CTE|DAE)\d+\.\d+)\s+'
            r'.+?\s+'
            r'(?:Online|Offline)\s+'
            r'(\S+)\s+'
            r'[\d.]+TB\s+'
            r'Member Disk\s+'
            r'\d+\s+'
            r'\S+\s+\S+\s+'
            r'(\S{10,})\s+'
            r'(\S+)'
        )

        for m in re.finditer(row_pattern, table_content):
            disk_id = m.group(1)
            disk_type = m.group(2)
            barcode = m.group(3)
            item = m.group(4)

            if disk_id in seen_ids:
                continue
            seen_ids.add(disk_id)

            desc = "N/A"

            detail_match = re.search(
                rf'Disk Frame and Slot ID:\s*{re.escape(disk_id)}\s*\n(.*?)(?=\n\s*Disk ID:|\Z)',
                self.content,
                re.DOTALL
            )
            if detail_match:
                detail_block = detail_match.group(1)
                elabel_m = re.search(
                    r'Disk Elabel:\s*(.*?)(?=\n\s*Disk [A-Z]|\Z)',
                    detail_block,
                    re.DOTALL
                )
                if elabel_m:
                    lbl = extract_label_fields(elabel_m.group(1))
                    if lbl["description"] != "N/A":
                        desc = lbl["description"]
                    if lbl["item"] != "N/A":
                        item = lbl["item"]

            name = desc if desc != "N/A" else disk_type

            components.append({
                "id":   disk_id,
                "name": name,
                "type": "Disk",
                "bom":  item,
            })

        return components

    # --------------------------------------------------------------------------
    # OCEANSTOR: POWER SUPPLY (без Elabel!)
    # --------------------------------------------------------------------------

    def parse_power_oceanstor(self):
        """Парсит Power Info OceanStor V3 (без Elabel)."""
        components = []
        seen_ids = set()

        pattern = (
            r'Power ID:\s*([A-Z]+\d+\.(?:PSU|POWER)\d+)\s*\n'
            r'(.*?)'
            r'(?=\n+\s*Power ID:|\n+[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            psu_id = m.group(1)
            if psu_id in seen_ids:
                continue
            seen_ids.add(psu_id)

            block = m.group(2)

            sn_m = re.search(r'SN:\s*(\S+)', block)
            sn = sn_m.group(1).strip() if sn_m else None

            bom = extract_bom_from_serial(sn)

            name = TEXT_NO_DESCRIPTION

            components.append({
                "id":   psu_id,
                "name": name,
                "type": "Power Supply",
                "bom":  bom,
            })

        return components

    # --------------------------------------------------------------------------
    # OCEANSTOR: FAN (с Elabel!)
    # --------------------------------------------------------------------------

    def parse_fan_oceanstor(self):
        """Парсит Fan Info OceanStor V3."""
        components = []
        seen_ids = set()

        pattern = (
            r'Fan ID:\s*([A-Z]+\d+(?:\.[A-Z])?\.FAN\d+)\s*\n'
            r'(.*?)'
            r'(?=\n+\s*Fan ID:|\n+[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            fan_id = m.group(1)
            if fan_id in seen_ids:
                continue
            seen_ids.add(fan_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Fan ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   fan_id,
                "name": name,
                "type": "Fan",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # OCEANSTOR: BBU (с Elabel, дубли в Controller 0/1!)
    # --------------------------------------------------------------------------

    def parse_bbu_oceanstor(self):
        """Парсит BBU Info OceanStor V3 (dedup по ID)."""
        components = []
        seen_ids = set()

        pattern = (
            r'BBU ID:\s*([A-Z]+\d+\.(?:PSU|BBU)\d+)\s*\n'
            r'(.*?)'
            r'(?=\n+\s*BBU ID:|\n+[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            bbu_id = m.group(1)
            if bbu_id in seen_ids:
                continue
            seen_ids.add(bbu_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=BBU ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   bbu_id,
                "name": name,
                "type": "BBU",
                "bom":  lbl["item"],
            })

        return components       
        
    # --------------------------------------------------------------------------
    # OCEANSTOR: I/O MODULE (с Elabel, дубли в Controller 0/1!)
    # --------------------------------------------------------------------------

    def parse_iom_oceanstor(self):
        """Парсит Interface Board OceanStor V3 (dedup по ID)."""
        components = []
        seen_ids = set()

        pattern = (
            r'Board ID:\s*(CTE\d+\.[A-Z]\.IOM\d+)\s*\n'
            r'(.*?)'
            r'(?=\n+\s*Board ID:|\n+[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            board_id = m.group(1)
            if board_id in seen_ids:
                continue
            seen_ids.add(board_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Board ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   board_id,
                "name": name,
                "type": "I/O Module",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # OCEANSTOR: EXPANDER BOARD (с Elabel, дубли в Controller 0/1!)
    # --------------------------------------------------------------------------

    def parse_expander_oceanstor(self):
        """Парсит Expander Board OceanStor V3 (dedup по ID)."""
        components = []
        seen_ids = set()

        pattern = (
            r'Board ID:\s*(DAE\d+\.[A-Z])\s*\n'
            r'(.*?)'
            r'(?=\n+\s*Board ID:|\n+[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            exp_id = m.group(1)
            if exp_id in seen_ids:
                continue
            seen_ids.add(exp_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=Board ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                continue

            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

            components.append({
                "id":   exp_id,
                "name": name,
                "type": "Expansion Board",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # OCEANSTOR: SFP (свой формат полей!)
    # --------------------------------------------------------------------------

    def parse_sfp_oceanstor(self):
        """Парсит SFP Info OceanStor V3."""
        components = []
        seen_serials = set()

        port_pattern = (
            r'ID:\s*([A-Z]+\d+\.[A-Z]+\.[A-Z]+\d+\.P\d+)\s*\n'
            r'(.*?)'
            r'(?=\n+\s*ID:|\n+[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        fc_port_pattern = r'ID:\s*(\S+\.P\d+)\s*\n'

        port_pattern = (
            r'ID:\s*([A-Z]+\d+\.[A-Z]+\.[A-Z]+\d+\.P\d+)\s*\n'
            r'(.*?)'
            r'(?=\n+\s*ID:|\n+[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(port_pattern, self.content, re.DOTALL):
            port_id = m.group(1)
            block = m.group(2)

            sfp_m = re.search(
                r'SFP Info:\s*\n(.*?)(?=\n+\s*(?:ID:|SFP Info:)|\n+[A-Z][A-Za-z ]+-{5,}|\Z)',
                block,
                re.DOTALL
            )
            if not sfp_m:
                continue

            sfp_block = sfp_m.group(1)

            vendor_m = re.search(r'Vendor Name:\s*(.+)', sfp_block)
            model_m = re.search(r'Vendor PN:\s*(.+)', sfp_block)
            sn_m = re.search(r'Vendor SN:\s*(\S+)', sfp_block)

            vendor = vendor_m.group(1).strip() if vendor_m else ""
            model = model_m.group(1).strip() if model_m else ""
            sn = sn_m.group(1).strip() if sn_m else ""

            if not vendor and not model:
                continue

            if sn and sn in seen_serials:
                continue
            if sn:
                seen_serials.add(sn)

            sfp_name = f"{vendor} {model}".strip()

            components.append({
                "id":   port_id,
                "name": sfp_name,
                "type": "SFP Module",
                "bom":  sfp_name,
            })

        return components