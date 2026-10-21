#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser_V5.py — парсер логов Huawei Storage V5.

Поддерживает два подтипа V5:
1. "Плоский" V5 (OceanStor 2600 V5) — Power/Fan/BBU/IOM/Expander/Enclosure
   идут в своих секциях верхнего уровня, поля: ID:, Power ID:, Fan ID:, BBU ID:, Board ID:.
2. "Вложенный" V5 (OceanStor 5110 / 5500 V5) — Power/Fan/BBU/IOM/Expander
   идут ВНУТРИ секции Controller N, поля: Power ID:, Fan ID:, BBU ID:, Board ID:.

Диски — всегда через таблицу "#### Disk Info ####" + детальные блоки
"Member Disk Info" с Disk Elabel (формат идентичен V6).

SFP — либо в отдельной секции "SFP----" (2600 V5), либо внутри
"SFP Info:" в ETH Port / SAS Port / FC Port (5110 / 5500 V5).

Каждый компонент — dict:
    {
        "id":   str,   # уникальный ID из лога
        "name": str,   # Description из Elabel (или заглушка)
        "type": str,   # тип компонента
        "bom":  str,   # Item из Elabel (или BOM из SN)
    }
"""

import re

from Utils.Utils_Regex_Helpers import (
    extract_label_fields,
    extract_bom_from_serial,
    make_name_from_label,
    make_bom_from_label_or_serial,
)
from Utils.Utils_Constants import TEXT_NO_DESCRIPTION


class V5Parser:
    """Парсер логов Huawei Storage V5 (OceanStor 2600 / 5110 / 5500 / ...)."""

    def __init__(self, content, sys_info):
        self.content = content
        self.sys_info = sys_info

    # --------------------------------------------------------------------------
    # ДИСПЕТЧЕР
    # --------------------------------------------------------------------------

    def parse_all(self, progress_callback=None):
        """Запускает все парсеры и возвращает общий список компонентов."""

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
    # 1. ENCLOSURES
    # --------------------------------------------------------------------------

    def parse_enclosures(self):
        """Парсит Enclosure Info (V5)."""
        components = []
        seen_ids = set()

        section_match = re.search(
            r'\nENCLOSURE-{5,}(.*?)(?=\n[A-Z][A-Za-z ]+-{5,}|\Z)',
            self.content,
            re.DOTALL
        )
        if not section_match:
            section_text = self.content
        else:
            section_text = section_match.group(1)

        pattern = (
            r'Enclosure ID:\s*((?:CTE|DAE|DSW)\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*Enclosure ID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, section_text, re.DOTALL):
            enc_id = m.group(1)
            if enc_id in seen_ids:
                continue
            seen_ids.add(enc_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=\n\s*Enclosure ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            sn_m = re.search(r'\bSN:\s*(\S+)', block)
            sn = sn_m.group(1).strip() if sn_m else None

            bom = make_bom_from_label_or_serial(lbl, serial=sn)
            name = make_name_from_label(lbl, fallback_text=TEXT_NO_DESCRIPTION)

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
    # 2. CONTROLLERS
    # --------------------------------------------------------------------------

    def parse_controllers(self):
        """Парсит контроллеры (0A, 0B, 0C, 0D)."""
        components = []
        seen_ids = set()

        pattern = (
            r'Controller ID:\s*(\d+[A-Z])\s*\n'
            r'(.*?)'
            r'(?=\n\s*Controller ID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            ctrl_id = m.group(1)
            if ctrl_id in seen_ids:
                continue
            seen_ids.add(ctrl_id)

            block = m.group(2)

            if "Electronic Label:" not in block and "CPU:" not in block:
                continue

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=\n\s*Controller ID:|\n\s*Management|\Z)',
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
    # 3. DISKS (таблица "#### Disk Info ####" + Member Disk Info)
    # --------------------------------------------------------------------------

    def parse_disks(self):
        """Парсит диски V5 (таблица Disk Info + Member Disk Info)."""
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
            r'\S+\s+'
            r'\S+\s+'
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
    # 4. POWER SUPPLY
    # --------------------------------------------------------------------------

    def parse_power(self):
        """Парсит блоки Power (ID: ... / Power ID: ...)."""
        components = []
        seen_ids = set()

        pattern = (
            r'(?:^|\n)\s*(?:Power )?ID:\s*'
            r'((?:CTE|DAE)\d+\.(?:PSU|POWER)\s*\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*(?:Power )?ID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            psu_id_raw = m.group(1)
            psu_id = re.sub(r'\s+', '', psu_id_raw)
            if psu_id in seen_ids:
                continue
            seen_ids.add(psu_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=\n\s*(?:Power )?ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            sn_m = re.search(r'Serial Number:\s*(\S+)', block)
            sn = sn_m.group(1).strip() if sn_m else None

            if lbl["item"] == "N/A":
                item_m = re.search(r'Item:\s*(\S+)', block)
                if item_m and item_m.group(1).strip() != "--":
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
    # 5. FAN
    # --------------------------------------------------------------------------

    def parse_fan(self):
        """Парсит блоки Fan (ID: ... / Fan ID: ...)."""
        components = []
        seen_ids = set()

        pattern = (
            r'(?:^|\n)\s*(?:Fan )?ID:\s*'
            r'((?:CTE|DAE)\d+(?:\.[A-Z])?\.(?:FAN|PSU)\s*\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*(?:Fan )?ID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            fan_id_raw = m.group(1)
            fan_id = re.sub(r'\s+', '', fan_id_raw)
            if fan_id in seen_ids:
                continue
            seen_ids.add(fan_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=\n\s*(?:Fan )?ID:|\Z)',
                block,
                re.DOTALL
            )
            if elabel_m:
                lbl = extract_label_fields(elabel_m.group(1))

            if lbl["item"] == "N/A":
                item_m = re.search(r'Item:\s*(\S+)', block)
                if item_m and item_m.group(1).strip() != "--":
                    lbl["item"] = item_m.group(1).strip()
                else:
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
    # 6. BBU
    # --------------------------------------------------------------------------

    def parse_bbu(self):
        """Парсит блоки BBU (ID: ... / BBU ID: ...)."""
        components = []
        seen_ids = set()

        pattern = (
            r'(?:^|\n)\s*(?:BBU )?ID:\s*'
            r'((?:CTE)\d+(?:\.(?:[A-Z]\.BBU|BBU\d+|\d+|[A-Z]\.\d+|PSU\d+)))\s*\n'
            r'(.*?)'
            r'(?=\n\s*(?:BBU )?ID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            bbu_id = m.group(1)
            if bbu_id in seen_ids:
                continue
            seen_ids.add(bbu_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=\n\s*(?:BBU )?ID:|\Z)',
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
    # 7. I/O MODULE (Interface Board)
    # --------------------------------------------------------------------------

    def parse_iom(self):
        """Парсит Interface Board (ID: ... / Board ID: CTE*)."""
        components = []
        seen_ids = set()

        pattern = (
            r'(?:^|\n)\s*(?:Board )?ID:\s*'
            r'(CTE\d+\.[A-Z]\.IOM\d+)\s*\n'
            r'(.*?)'
            r'(?=\n\s*(?:Board )?ID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            board_id = m.group(1)
            if board_id in seen_ids:
                continue
            seen_ids.add(board_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=\n\s*(?:Board )?ID:|\Z)',
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
    # 8. EXPANDER BOARD
    # --------------------------------------------------------------------------

    def parse_expander(self):
        """Парсит Expander Board (ID: ... / Board ID: DAE*)."""
        components = []
        seen_ids = set()

        pattern = (
            r'(?:^|\n)\s*(?:Board )?ID:\s*'
            r'(DAE\d+\.[A-Z])\s*\n'
            r'(.*?)'
            r'(?=\n\s*(?:Board )?ID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )

        for m in re.finditer(pattern, self.content, re.DOTALL):
            exp_id = m.group(1)
            if exp_id in seen_ids:
                continue
            seen_ids.add(exp_id)

            block = m.group(2)

            lbl = {"description": "N/A", "barcode": "N/A", "item": "N/A"}
            elabel_m = re.search(
                r'Electronic Label:\s*(.*?)(?=\n\s*(?:Board )?ID:|\Z)',
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
    # 9. SFP MODULE
    # --------------------------------------------------------------------------

    def parse_sfp(self):
        """Парсит SFP-модули (плоский и вложенный варианты)."""
        components = []
        seen_serials = set()

        sfp_section_match = re.search(
            r'\nSFP-{5,}(.*?)(?=\n[A-Z][A-Za-z ]+-{5,}|\Z)',
            self.content,
            re.DOTALL
        )
        if sfp_section_match:
            sfp_section = sfp_section_match.group(1)
            pattern = (
                r'PortID:\s*(\S+)\s*\n'
                r'(.*?)'
                r'(?=\n\s*PortID:|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
            )
            for m in re.finditer(pattern, sfp_section, re.DOTALL):
                sfp_id = m.group(1)
                block = m.group(2)
                self._add_sfp(components, seen_serials, sfp_id, block)

        pattern = (
            r'(?:^|\n)\s*ID:\s*(\S+)\s*\n'
            r'(.*?)'
            r'SFP Info:\s*\n(.*?)'
            r'(?=\n\s*(?:ID:|SFP Info:)|\n[A-Z][A-Za-z ]+-{5,}|\Z)'
        )
        for m in re.finditer(pattern, self.content, re.DOTALL):
            port_id = m.group(1)
            sfp_block = m.group(3)
            self._add_sfp(components, seen_serials, port_id, sfp_block)

        return components

    def _add_sfp(self, components, seen_serials, sfp_id, block):
        """Вспомогательный метод: извлекает SFP и добавляет в список.

        Поддерживает оба формата полей:
            V5: Vendor Name / Vendor PN / Vendor SN
            V3: Vendor / Model / SN
        """
        vendor_m = (re.search(r'Vendor\s+Name:\s*(.+)', block)
                    or re.search(r'Vendor:\s*(.+)', block))
        model_m  = (re.search(r'Vendor\s+PN:\s*(.+)', block)
                    or re.search(r'Model:\s*(.+)', block))
        sn_m     = (re.search(r'Vendor\s+SN:\s*(\S+)', block)
                    or re.search(r'SN:\s*(\S+)', block))

        vendor = vendor_m.group(1).strip() if vendor_m else ""
        model  = model_m.group(1).strip()  if model_m  else ""
        sn     = sn_m.group(1).strip()     if sn_m     else ""

        if not vendor and not model:
            return

        if sn and sn in seen_serials:
            return
        if sn:
            seen_serials.add(sn)

        sfp_name = f"{vendor} {model}".strip()

        components.append({
            "id":   sfp_id,
            "name": sfp_name,
            "type": "SFP Module",
            "bom":  sfp_name,
        })
