#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core_CRM_Checker.py — модуль интеграции с CRM2 (поиск остатков).
"""

import os
import urllib3
import requests
from requests_ntlm import HttpNtlmAuth

# Отключаем предупреждения SSL (так как используется самоподписанный сертификат)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Базовый URL (пока dev-стенд, потом вынесем в настройки)
CRM_BASE_URL = "https://crm2-develop.hostco.ru:1337/"

# GUID статусов из CRM2
STATUS_READY_ID = "6e9b5a99-a785-4dba-8d44-fe434f92e03a" # Готово к использованию
STATUS_REF_ID = "b5d278cb-9875-499a-b732-1d8328fb04ff"   # REF


class CRMChecker:
    """Класс для работы с API CRM2."""

    def __init__(self, username=None, password=None):
        # Если креды не переданы явно, пытаемся взять их из переменных окружения
        self.username = username or os.getenv("CRM_USER")
        self.password = password or os.getenv("CRM_PASS")
        
        self.session = requests.Session()
        if self.username and self.password:
            self.session.auth = HttpNtlmAuth(self.username, self.password)
            
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8"
        })

    def check_connection(self) -> bool:
        """Проверяет доступность API (запрашивает список статусов)."""
        url = CRM_BASE_URL + "api/SparePartStatuses/All"
        try:
            # Таймаут ставим небольшой, чтобы не вешать GUI
            r = self.session.get(url, verify=False, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def get_stock_qty(self, part_number: str) -> int:
        """
        Возвращает количество запчастей на складе со статусом 'Готово к использованию'.
        Пока возвращает 0, так как эндпоинт FilteredSpareParts отдает 401.
        """
        if not part_number or not self.username:
            return 0

        # Заглушка для будущей логики:
        # url = CRM_BASE_URL + "api/SpareParts/FilteredSpareParts"
        # payload = {"sparePartPartNumberFilter": part_number, ...}
        # r = self.session.post(url, json=payload, verify=False, timeout=5)
        # if r.status_code == 200:
        #     data = r.json()
        #     spare_parts = data.get("spareParts", [])
        #     count = sum(1 for p in sp if p.get("sparePartStatusId") == STATUS_READY_ID)
        #     return count

        return 0  # Временно