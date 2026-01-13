"""
Scraper pro jobs.cz
Vyhledává pracovní nabídky na jobs.cz
"""

from datetime import datetime
from typing import List, Dict
import urllib.parse

from .base_scraper import BaseScraper

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class JobsCzScraper(BaseScraper):
    """
    Scraper pro jobs.cz

    POZNÁMKA: HTML selektory jsou ukázkové a musí být upraveny
    podle skutečné struktury stránky jobs.cz. Struktura webu
    se může časem měnit.
    """

    def __init__(self):
        """Inicializace jobs.cz scraperu"""
        super().__init__("jobs_cz")
        self.base_url = config.TARGET_PORTALS["jobs_cz"]["base_url"]

    def _build_search_url(self, keyword: str) -> str:
        """
        Sestaví search URL pro jobs.cz

        Args:
            keyword: Klíčové slovo pro vyhledávání

        Returns:
            URL string
        """
        # Příklad URL struktury - může se lišit
        # https://www.jobs.cz/prace/?q=project+manager
        encoded_keyword = urllib.parse.quote_plus(keyword)
        return f"{self.base_url}/prace/?q={encoded_keyword}"

    def scrape(self, keywords: List[str]) -> List[Dict]:
        """
        Scrapuje jobs.cz pro zadaná klíčová slova

        Args:
            keywords: Seznam klíčových slov

        Returns:
            Seznam slovníků s nabídkami
        """
        all_jobs = []
        self.logger.info(f"Začínám scraping jobs.cz s {len(keywords)} klíčovými slovy")

        for keyword in keywords:
            self.logger.info(f"Hledám: {keyword}")
            search_url = self._build_search_url(keyword)

            response = self._make_request(search_url)
            if not response:
                self.logger.warning(f"Nepodařilo se získat výsledky pro '{keyword}'")
                continue

            soup = self._parse_html(response.text)
            if not soup:
                continue

            jobs = self._extract_jobs_from_page(soup, keyword)
            all_jobs.extend(jobs)

            self.logger.info(f"Nalezeno {len(jobs)} nabídek pro '{keyword}'")

        self.logger.info(f"Celkem nalezeno {len(all_jobs)} nabídek na jobs.cz")
        return all_jobs

    def _extract_jobs_from_page(self, soup, keyword: str) -> List[Dict]:
        """
        Extrahuje nabídky ze stránky s výsledky

        Args:
            soup: BeautifulSoup objekt
            keyword: Klíčové slovo (pro kontext)

        Returns:
            Seznam slovníků s nabídkami

        POZNÁMKA: Selektory jsou UKÁZKOVÉ a musí být upraveny
        podle skutečné HTML struktury jobs.cz
        """
        jobs = []

        # PŘÍKLAD selektorů - MUSÍ BÝT UPRAVENO podle skutečné struktury
        # Toto je pouze demonstrační kód
        job_listings = soup.find_all('article', class_='standalone-job-item')

        if not job_listings:
            # Zkusit alternativní selektory
            job_listings = soup.find_all('div', class_='search-list__item')

        if not job_listings:
            self.logger.warning("Nenalezeny žádné job listings (možná změna HTML struktury)")
            return jobs

        for job_elem in job_listings:
            try:
                job_data = self._extract_job_details(job_elem)
                if job_data:
                    jobs.append(job_data)
            except Exception as e:
                self.logger.error(f"Chyba při extrakci nabídky: {e}", exc_info=True)
                continue

        return jobs

    def _extract_job_details(self, job_element) -> Dict:
        """
        Extrahuje detaily o nabídce z HTML elementu

        Args:
            job_element: BeautifulSoup element

        Returns:
            Slovník s daty nebo None

        POZNÁMKA: Toto je UKÁZKOVÝ kód. Skutečné selektory HTML
        musí být upraveny podle aktuální struktury jobs.cz
        """
        try:
            # PŘÍKLADY extrakce - MUSÍ BÝT UPRAVENO
            # Název pozice
            nazev_elem = job_element.find('h2', class_='standalone-job-item__title')
            if not nazev_elem:
                nazev_elem = job_element.find('a', class_='search-list__main-info__title__link')

            nazev_pozice = nazev_elem.get_text(strip=True) if nazev_elem else "N/A"

            # URL
            url_elem = job_element.find('a', href=True)
            url = url_elem['href'] if url_elem else ""
            if url and not url.startswith('http'):
                url = self.base_url + url

            # Společnost
            spolecnost_elem = job_element.find('span', class_='standalone-job-item__employer')
            if not spolecnost_elem:
                spolecnost_elem = job_element.find('li', class_='search-list__main-info__employer')

            spolecnost = spolecnost_elem.get_text(strip=True) if spolecnost_elem else "N/A"

            # Lokace
            lokace_elem = job_element.find('span', class_='standalone-job-item__locality')
            if not lokace_elem:
                lokace_elem = job_element.find('li', class_='search-list__main-info__locality')

            lokace = lokace_elem.get_text(strip=True) if lokace_elem else "N/A"

            # Mzda (není vždy uvedena)
            mzda_elem = job_element.find('span', class_='standalone-job-item__salary')
            mzda = mzda_elem.get_text(strip=True) if mzda_elem else None

            # Typ úvazku (pokud je uveden)
            typ_uvazku = "N/A"
            typ_elem = job_element.find('span', class_='job-type')
            if typ_elem:
                typ_uvazku = typ_elem.get_text(strip=True)

            # Sestavení výsledku
            job_data = {
                'nazev_pozice': nazev_pozice,
                'spolecnost': spolecnost,
                'lokace': lokace,
                'typ_uvazku': typ_uvazku,
                'url': url,
                'mzda': mzda,
                'portal': 'jobs.cz',
                'datum_nalezeni': datetime.now().strftime('%Y-%m-%d'),
            }

            return job_data

        except Exception as e:
            self.logger.error(f"Chyba při parsování job elementu: {e}", exc_info=True)
            return None
