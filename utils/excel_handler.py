"""
Modul pro práci s Excel soubory
Čtení, zápis a aktualizace pracovních nabídek
"""

import os
import logging
from typing import List, Dict, Set
from datetime import datetime
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class ExcelHandler:
    """
    Třída pro správu Excel souboru s pracovními nabídkami

    Funkce:
    - Vytvoření nového Excel souboru
    - Načtení existujících záznamů
    - Přidání nových nabídek
    - Aktualizace existujících záznamů
    - Získání seznamu ID pro deduplikaci
    """

    def __init__(self, file_path: str = None):
        """
        Inicializace Excel handleru

        Args:
            file_path: Cesta k Excel souboru (default z configu)
        """
        self.file_path = file_path or config.EXCEL_OUTPUT_FILE
        self.logger = logging.getLogger("excel_handler")
        self.workbook = None
        self.worksheet = None
        self.records_added = 0  # Počítadlo přidaných záznamů

    def _create_new_file(self):
        """Vytvoří nový Excel soubor se strukturou"""
        self.logger.info(f"Vytvářím nový Excel soubor: {self.file_path}")

        self.workbook = Workbook()
        self.worksheet = self.workbook.active
        self.worksheet.title = config.EXCEL_SHEET_NAME

        # Vytvoření hlavičky
        headers = config.EXCEL_COLUMNS

        # Nastavení stylů pro hlavičku
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        for col_num, header in enumerate(headers, start=1):
            cell = self.worksheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # Nastavení šířky sloupců
        column_widths = {
            'A': 32,  # ID
            'B': 12,  # Datum nalezení
            'C': 40,  # Název pozice
            'D': 30,  # Společnost
            'E': 20,  # Lokace
            'F': 15,  # Typ úvazku
            'G': 15,  # Portál
            'H': 50,  # URL
            'I': 15,  # Mzda
            'J': 10,  # Relevance
            'K': 10,  # Status
            'L': 40,  # Poznámky
        }

        for col, width in column_widths.items():
            self.worksheet.column_dimensions[col].width = width

        # Uložení souboru
        self.workbook.save(self.file_path)
        self.logger.info("Nový Excel soubor vytvořen")

    def load_or_create(self):
        """Načte existující soubor nebo vytvoří nový"""
        if os.path.exists(self.file_path):
            self.logger.info(f"Načítám existující soubor: {self.file_path}")
            try:
                self.workbook = openpyxl.load_workbook(self.file_path)
                self.worksheet = self.workbook[config.EXCEL_SHEET_NAME]
            except Exception as e:
                self.logger.error(f"Chyba při načítání souboru: {e}")
                self.logger.info("Vytvářím nový soubor místo toho")
                self._create_new_file()
        else:
            self._create_new_file()

    def get_existing_ids(self) -> Set[str]:
        """
        Vrátí množinu všech existujících ID v Excel souboru

        Returns:
            Set ID pro deduplikaci
        """
        if not self.worksheet:
            self.load_or_create()

        existing_ids = set()

        # Iterace přes řádky (skip header)
        for row in self.worksheet.iter_rows(min_row=2, values_only=True):
            if row[0]:  # ID je v prvním sloupci
                existing_ids.add(row[0])

        self.logger.info(f"Načteno {len(existing_ids)} existujících ID")
        return existing_ids

    def add_job(self, job_data: Dict) -> bool:
        """
        Přidá novou pracovní nabídku do Excel souboru

        Args:
            job_data: Slovník s daty nabídky

        Returns:
            True pokud byla nabídka přidána, False při chybě

        Očekávaná struktura job_data:
        {
            'id': str,
            'datum_nalezeni': str,
            'nazev_pozice': str,
            'spolecnost': str,
            'lokace': str,
            'typ_uvazku': str,
            'portal': str,
            'url': str,
            'mzda': str,
            'relevance': str,
            'status': str,
            'poznamky': str,
        }
        """
        if not self.worksheet:
            self.load_or_create()

        try:
            # Najít další volný řádek
            next_row = self.worksheet.max_row + 1

            # Mapování dat na sloupce
            row_data = [
                job_data.get('id', ''),
                job_data.get('datum_nalezeni', ''),
                job_data.get('nazev_pozice', ''),
                job_data.get('spolecnost', ''),
                job_data.get('lokace', ''),
                job_data.get('typ_uvazku', ''),
                job_data.get('portal', ''),
                job_data.get('url', ''),
                job_data.get('mzda', ''),
                job_data.get('relevance', config.DEFAULT_RELEVANCE),
                job_data.get('status', config.DEFAULT_STATUS),
                job_data.get('poznamky', ''),
            ]

            # Zápis dat do řádku
            for col_num, value in enumerate(row_data, start=1):
                cell = self.worksheet.cell(row=next_row, column=col_num, value=value)

                # Sloupec H (8) obsahuje URL - formátovat jako hyperlink
                if col_num == 8 and value:  # URL sloupec
                    cell.hyperlink = value
                    cell.style = "Hyperlink"

            # Zvýraznění řádku podle relevance
            if job_data.get('relevance') == 'High':
                fill = PatternFill(start_color="E7F4E4", end_color="E7F4E4", fill_type="solid")
                for col_num in range(1, len(row_data) + 1):
                    self.worksheet.cell(row=next_row, column=col_num).fill = fill

            self.logger.debug(f"Přidána nabídka: {job_data.get('nazev_pozice')} @ {job_data.get('spolecnost')}")
            self.records_added += 1  # Inkrementace počítadla
            return True

        except Exception as e:
            self.logger.error(f"Chyba při přidávání nabídky: {e}", exc_info=True)
            return False

    def add_jobs_batch(self, jobs: List[Dict]) -> int:
        """
        Přidá seznam nabídek najednou

        Args:
            jobs: Seznam slovníků s daty nabídek

        Returns:
            Počet úspěšně přidaných nabídek
        """
        if not self.worksheet:
            self.load_or_create()

        added_count = 0

        for job in jobs:
            if self.add_job(job):
                added_count += 1

        self.logger.info(f"Přidáno {added_count}/{len(jobs)} nabídek")
        return added_count

    def save(self):
        """Uloží změny do Excel souboru (pouze pokud byly přidány nové záznamy)"""
        if not self.workbook:
            self.logger.warning("Není co ukládat - workbook není načtený")
            return

        if self.records_added == 0:
            self.logger.info("Žádné nové záznamy nepřidány - ukládání přeskočeno")
            return

        try:
            self.workbook.save(self.file_path)
            self.logger.info(f"Excel soubor uložen: {self.file_path} ({self.records_added} nových záznamů)")
        except Exception as e:
            self.logger.error(f"Chyba při ukládání souboru: {e}", exc_info=True)

    def close(self):
        """Zavře workbook"""
        if self.workbook:
            self.workbook.close()
            self.workbook = None
            self.worksheet = None
