#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser_V6.py — парсер логов Huawei OceanStor Dorado V6.

Класс V6Parser разбирает содержимое лога и возвращает список компонентов.
Каждый компонент — dict:
    {
        "id":   str,   # уникальный ID из лога (например, "DAE000.0")
        "name": str,   # Description из Electronic Label (для колонки K)
        "type": str,   # тип ("Disk", "Power Supply", "Fan", ...)
        "bom":  str,   # Item из Elabel (для группировки → колонка M)
    }

Особые случаи:
- Enclosure: для CTE0 тип "Enclosure", для DAE* — тот же тип "Enclosure",
  но в Excel разделяются по префиксу ID (CTE → Storage, DAE → Disk Enclosure).
- SFP: "bom" = "Vendor Model" (BOM в логе отсутствует для SFP).
- IOM: name = Description из Elabel.
"""

import re
from Utils_Regex_Helpers import extract_label_fields


class V6Parser:
    """Парсер компонентов из лога Huawei OceanStor Dorado V6."""

    def __init__(self, content, sys_info):
        """
        :param content: полный текст лога (str)
        :param sys_info: dict с полями name/serial/model/version (используется редко)
        """
        self.content = content
        self.sys_info = sys_info

    # --------------------------------------------------------------------------
    # ДИСПЕТЧЕР
    # --------------------------------------------------------------------------

    def parse_all(self, progress_callback=None):
        """Запускает все парсеры и возвращает общий список компонентов.

        :param progress_callback: опциональный callback (step_text, percent)
        """
        def _notify(text, percent):
            if progress_callback:
                progress_callback(text, percent)

        components = []

        _notify("Parsing enclosures...", 20)
        components.extend(self.parse_enclosures())

        _notify("Parsing controllers...", 30)
        components.extend(self.parse_controllers())

        _notify("Parsing disks...", 45)
        components.extend(self.parse_disks())

        _notify("Parsing power supplies...", 55)
        components.extend(self.parse_power())

        _notify("Parsing fans...", 65)
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
    # 1. ENCLOSURES (CTE0, DAE000, DAE020)
    # --------------------------------------------------------------------------

    def parse_enclosures(self):
        components = []
        seen_ids = set()

        pattern = r'Enclosure\((CTE\d+|DAE\d+)\)-+\n(.*?)(?=\s*Enclosure\((?:CTE|DAE)\d+\)|\Z)'
        for m in re.finditer(pattern, self.content, re.DOTALL):
            enc_id = m.group(1)
            if enc_id in seen_ids:
                continue
            seen_ids.add(enc_id)

            block = m.group(2)
            lbl = extract_label_fields(block)

            if lbl["item"] == "N/A" and lbl["barcode"] == "N/A":
                continue

            components.append({
                "id":   enc_id,
                "name": lbl["description"],
                "type": "Enclosure",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 2. CONTROLLERS (Control Board 0A, 0B, 0C, 0D)
    # --------------------------------------------------------------------------

    def parse_controllers(self):
        components = []
        seen_ids = set()

        pattern = r'Control Board\((\d+[A-Z])\)-+\n(.*?)(?=\s*Control Board\(\d+[A-Z]\)|\Z)'
        for m in re.finditer(pattern, self.content, re.DOTALL):
            ctrl_id = m.group(1)
            if ctrl_id in seen_ids:
                continue
            seen_ids.add(ctrl_id)

            block = m.group(2)
            lbl = extract_label_fields(block)

            if lbl["item"] == "N/A" and lbl["barcode"] == "N/A":
                continue

            components.append({
                "id":   ctrl_id,
                "name": lbl["description"],
                "type": "Controller",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 3. DISKS (из блока "Disk Info" + детальные Elabel из "Member Disk Info")
    # --------------------------------------------------------------------------

    def parse_disks(self):
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
            detail_block_match = re.search(
                rf'Disk Frame and Slot ID:\s*{re.escape(disk_id)}.*?Disk Elabel:(.*?)/\$ElabelVersion',
                self.content,
                re.DOTALL
            )
            if detail_block_match:
                lbl = extract_label_fields(detail_block_match.group(1))
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
    # 4. POWER SUPPLY (Power(CTE0.PSU0), Power(DAE000.PSU0) и т.д.)
    # --------------------------------------------------------------------------

    def parse_power(self):
        components = []
        seen_ids = set()

        pattern = r'Power\((CTE\d+\.PSU\d+|DAE\d+\.PSU\d+)\)-+\n(.*?)(?=\s*Power\((?:CTE|DAE)\d+\.PSU\d+\)|\Z)'
        for m in re.finditer(pattern, self.content, re.DOTALL):
            psu_id = m.group(1)
            if psu_id in seen_ids:
                continue
            seen_ids.add(psu_id)

            block = m.group(2)
            lbl = extract_label_fields(block)

            if lbl["item"] == "N/A":
                continue

            components.append({
                "id":   psu_id,
                "name": lbl["description"],
                "type": "Power Supply",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 5. FAN (Fan(CTE0.A.FAN0), Fan(DAE000.A.FAN0) и т.д.)
    # --------------------------------------------------------------------------

    def parse_fan(self):
        components = []
        seen_ids = set()

        pattern = r'Fan\(((?:CTE|DAE)\d+\.[A-Z]\.FAN\d+)\)-+\n(.*?)(?=\s*Fan\((?:CTE|DAE)\d+\.[A-Z]\.FAN\d+\)|\Z)'
        for m in re.finditer(pattern, self.content, re.DOTALL):
            fan_id = m.group(1)
            if fan_id in seen_ids:
                continue
            seen_ids.add(fan_id)

            block = m.group(2)
            lbl = extract_label_fields(block)

            if lbl["item"] == "N/A":
                continue

            components.append({
                "id":   fan_id,
                "name": lbl["description"],
                "type": "Fan",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 6. BBU (BBU(CTE0.A.BBU), BBU(CTE0.B.BBU), ...)
    # --------------------------------------------------------------------------

    def parse_bbu(self):
        components = []
        seen_ids = set()

        pattern = r'BBU\(((?:CTE\d+\.(?:[A-Z]\.BBU|BBU\d+)))\)-+\n(.*?)(?=\s*BBU\((?:CTE\d+\.(?:[A-Z]\.BBU|BBU\d+))\)|\Z)'
        for m in re.finditer(pattern, self.content, re.DOTALL):
            bbu_id = m.group(1)
            if bbu_id in seen_ids:
                continue
            seen_ids.add(bbu_id)

            block = m.group(2)
            lbl = extract_label_fields(block)

            if lbl["item"] == "N/A":
                continue

            components.append({
                "id":   bbu_id,
                "name": lbl["description"],
                "type": "BBU",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 7. I/O MODULE (Interface Board CTE0.IOM.H0, CTE0.SMM0 и т.д.)
    # --------------------------------------------------------------------------

    def parse_iom(self):
        components = []
        seen_ids = set()

        pattern = r'Interface Board\(([^)]+)\)-+\n(.*?)(?=\s*Interface Board\([^)]+\)|\Z)'
        for m in re.finditer(pattern, self.content, re.DOTALL):
            board_id = m.group(1)
            if board_id in seen_ids:
                continue
            seen_ids.add(board_id)

            block = m.group(2)
            lbl = extract_label_fields(block)

            if lbl["item"] == "N/A":
                continue

            components.append({
                "id":   board_id,
                "name": lbl["description"],
                "type": "I/O Module",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 8. EXPANDER BOARD (Expander Board DAE000.A, DAE000.B, DAE020.A, DAE020.B)
    # --------------------------------------------------------------------------

    def parse_expander(self):
        components = []
        seen_ids = set()

        pattern = r'Expander Board\(([^)]+)\)-+\n(.*?)(?=\s*Expander Board\([^)]+\)|\Z)'
        for m in re.finditer(pattern, self.content, re.DOTALL):
            exp_id = m.group(1)
            if exp_id in seen_ids:
                continue
            seen_ids.add(exp_id)

            block = m.group(2)
            lbl = extract_label_fields(block)

            if lbl["item"] == "N/A":
                continue

            components.append({
                "id":   exp_id,
                "name": lbl["description"],
                "type": "Expansion Board",
                "bom":  lbl["item"],
            })

        return components

    # --------------------------------------------------------------------------
    # 9. SFP MODULE
    # --------------------------------------------------------------------------

    def parse_sfp(self):
        components = []
        seen_ids = set()
        seen_serials = set()

        pattern = r'SFP\(([^)]+)\)-+\n(.*?)(?=\s*SFP\([^)]+\)|\Z)'
        for m in re.finditer(pattern, self.content, re.DOTALL):
            sfp_id = m.group(1)
            if sfp_id in seen_ids:
                continue

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

            seen_ids.add(sfp_id)

            sfp_name = f"{vendor} {model}".strip()

            components.append({
                "id":   sfp_id,
                "name": sfp_name,
                "type": "SFP Module",
                "bom":  sfp_name,
            })

        return components
