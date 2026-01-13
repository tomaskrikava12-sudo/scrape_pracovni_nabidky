"""
Modul pro hodnocení relevance pracovních nabídek
Scoring na základě profilu kandidáta a klíčových slov
"""

import logging
from typing import Dict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class RelevanceScorer:
    """
    Třída pro hodnocení relevance pracovních nabídek

    Hodnotí na základě:
    - Klíčových slov pro vysokou relevanci
    - Profilu kandidáta
    - Lokace
    - Typu úvazku
    """

    def __init__(self):
        """Inicializace relevance scoreru"""
        self.logger = logging.getLogger("relevance_scorer")
        self.high_relevance_keywords = [kw.lower() for kw in config.HIGH_RELEVANCE_KEYWORDS]
        self.preferred_locations = [loc.lower() for loc in config.CANDIDATE_PROFILE.get("lokace_preferovana", [])]

    def score_job(self, job_data: Dict) -> str:
        """
        Vyhodnotí relevanci pracovní nabídky

        Args:
            job_data: Slovník s daty nabídky
                {
                    'nazev_pozice': str,
                    'spolecnost': str,
                    'lokace': str,
                    'typ_uvazku': str,
                    'popis': str,  # volitelný
                }

        Returns:
            "High" nebo "Medium"
        """
        score = 0

        # Získání dat pro vyhodnocení
        nazev = (job_data.get('nazev_pozice', '') or '').lower()
        lokace = (job_data.get('lokace', '') or '').lower()
        typ_uvazku = (job_data.get('typ_uvazku', '') or '').lower()
        popis = (job_data.get('popis', '') or '').lower()

        # Kombinovaný text pro vyhledávání klíčových slov
        full_text = f"{nazev} {lokace} {typ_uvazku} {popis}"

        # Hodnocení podle klíčových slov
        keyword_matches = 0
        for keyword in self.high_relevance_keywords:
            if keyword in full_text:
                keyword_matches += 1

        # Body za klíčová slova (max 50 bodů)
        score += min(keyword_matches * 10, 50)

        # Body za lokaci (30 bodů)
        if any(pref_loc in lokace for pref_loc in self.preferred_locations):
            score += 30

        # Body za remote/hybrid (20 bodů)
        if 'remote' in typ_uvazku or 'remote' in full_text:
            score += 20
        elif 'hybrid' in typ_uvazku or 'hybrid' in full_text:
            score += 15

        # Body za senior pozici (15 bodů)
        if 'senior' in nazev or 'lead' in nazev or 'head' in nazev:
            score += 15

        # Body za e-commerce zaměření (25 bodů)
        if 'e-commerce' in full_text or 'ecommerce' in full_text or 'eshop' in full_text:
            score += 25

        # Hodnocení podle celkového skóre
        if score >= 50:
            relevance = "High"
        else:
            relevance = "Medium"

        self.logger.debug(
            f"Relevance skóre: {score} -> {relevance} "
            f"pro '{job_data.get('nazev_pozice', 'N/A')}' @ '{job_data.get('spolecnost', 'N/A')}'"
        )

        return relevance

    def filter_by_minimum_relevance(self, jobs: list, min_relevance: str = "Medium") -> list:
        """
        Filtruje nabídky podle minimální relevance

        Args:
            jobs: Seznam slovníků s nabídkami
            min_relevance: Minimální relevance ("High" nebo "Medium")

        Returns:
            Filtrovaný seznam nabídek
        """
        if min_relevance == "High":
            return [job for job in jobs if job.get('relevance') == "High"]
        else:
            # Medium zahrnuje i High
            return jobs

    def add_relevance_to_jobs(self, jobs: list) -> list:
        """
        Přidá relevance skóre ke každé nabídce v seznamu

        Args:
            jobs: Seznam slovníků s nabídkami

        Returns:
            Seznam nabídek s přidanou relevancí
        """
        for job in jobs:
            if 'relevance' not in job or not job['relevance']:
                job['relevance'] = self.score_job(job)

        return jobs
