"""
Modul pro deduplikaci pracovních nabídek
Generuje unikátní hashe a kontroluje duplicity
"""

import hashlib
import logging
from typing import Dict, Set


class Deduplicator:
    """
    Třída pro správu deduplikace pracovních nabídek

    Používá hash z kombinace název_pozice + společnost + lokace
    pro identifikaci duplicitních záznamů
    """

    def __init__(self):
        """Inicializace deduplikátoru"""
        self.logger = logging.getLogger("deduplicator")
        self.seen_hashes: Set[str] = set()

    @staticmethod
    def generate_job_id(nazev_pozice: str, spolecnost: str, lokace: str) -> str:
        """
        Generuje unikátní ID (hash) pro pracovní nabídku

        Args:
            nazev_pozice: Název pracovní pozice
            spolecnost: Název společnosti
            lokace: Lokace práce

        Returns:
            Hexadecimální hash string (MD5)
        """
        # Normalizace - lowercase, strip whitespace
        nazev_normalized = (nazev_pozice or "").lower().strip()
        spolecnost_normalized = (spolecnost or "").lower().strip()
        lokace_normalized = (lokace or "").lower().strip()

        # Vytvoření unikátního stringu
        unique_string = f"{nazev_normalized}|{spolecnost_normalized}|{lokace_normalized}"

        # Generování MD5 hashe
        hash_object = hashlib.md5(unique_string.encode('utf-8'))
        return hash_object.hexdigest()

    def is_duplicate(self, job_id: str) -> bool:
        """
        Zkontroluje, zda ID již bylo viděno (je duplicitní)

        Args:
            job_id: Hash ID nabídky

        Returns:
            True pokud je duplicita, False pokud ne
        """
        return job_id in self.seen_hashes

    def add_job_id(self, job_id: str):
        """
        Přidá job ID do množiny viděných ID

        Args:
            job_id: Hash ID nabídky
        """
        self.seen_hashes.add(job_id)

    def load_existing_ids(self, existing_ids: Set[str]):
        """
        Načte existující ID z Excel souboru pro kontrolu duplicit

        Args:
            existing_ids: Množina existujících ID
        """
        self.seen_hashes = existing_ids.copy()
        self.logger.info(f"Načteno {len(self.seen_hashes)} existujících ID pro kontrolu duplicit")

    def check_and_add(self, nazev_pozice: str, spolecnost: str, lokace: str) -> tuple[str, bool]:
        """
        Zkontroluje duplicitu a přidá do cache pokud není duplicita

        Args:
            nazev_pozice: Název pracovní pozice
            spolecnost: Název společnosti
            lokace: Lokace práce

        Returns:
            Tuple (job_id, is_duplicate) - ID a boolean zda je duplicita
        """
        job_id = self.generate_job_id(nazev_pozice, spolecnost, lokace)
        is_dup = self.is_duplicate(job_id)

        if not is_dup:
            self.add_job_id(job_id)
            self.logger.debug(f"Nová nabídka přidána: {nazev_pozice} @ {spolecnost}")
        else:
            self.logger.debug(f"Duplicita nalezena: {nazev_pozice} @ {spolecnost}")

        return job_id, is_dup

    def get_stats(self) -> Dict[str, int]:
        """
        Vrátí statistiky o deduplikaci

        Returns:
            Slovník se statistikami
        """
        return {
            "total_unique_jobs": len(self.seen_hashes)
        }
