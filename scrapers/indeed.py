"""
Scraper pro Indeed.cz
Vyhledává pracovní nabídky na Indeed.cz
"""

from datetime import datetime
from typing import List, Dict
import urllib.parse

from .base_scraper import BaseScraper

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class IndeedScraper(BaseScraper):
    """
    Scraper pro Indeed.cz

    POZNÁMKA: HTML selektory jsou ukázkové a musí být upraveny
    podle skutečné struktury stránky
    """

    def __init__(self):
        """Inicializace Indeed.cz scraperu"""
        super().__init__("indeed")
        self.base_url = config.TARGET_PORTALS["indeed"]["base_url"]

    def _build_search_url(self, keyword: str) -> str:
        """Sestaví search URL pro Indeed.cz"""
        encoded_keyword = urllib.parse.quote_plus(keyword)
        return f"{self.base_url}/jobs?q={encoded_keyword}&l=Czech+Republic"

    def scrape(self, keywords: List[str]) -> List[Dict]:
        """Scrapuje Indeed.cz pro zadaná klíčová slova"""
        all_jobs = []
        self.logger.info(f"Začínám scraping Indeed.cz s {len(keywords)} klíčovými slovy")

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

        self.logger.info(f"Celkem nalezeno {len(all_jobs)} nabídek na Indeed.cz")
        return all_jobs

    def _extract_jobs_from_page(self, soup, keyword: str) -> List[Dict]:
        """Extrahuje nabídky ze stránky s výsledky"""
        jobs = []

        # UKÁZKOVÉ selektory pro Indeed
        job_listings = soup.find_all('div', class_='job_seen_beacon')

        if not job_listings:
            job_listings = soup.find_all('a', class_='tapItem')

        if not job_listings:
            self.logger.warning("Nenalezeny žádné job listings")
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
        """Extrahuje detaily o nabídce z HTML elementu"""
        try:
            # Název pozice
            nazev_elem = job_element.find('h2', class_='jobTitle')
            if not nazev_elem:
                nazev_elem = job_element.find('span', attrs={'title': True})

            nazev_pozice = nazev_elem.get_text(strip=True) if nazev_elem else "N/A"

            # URL
            url_elem = job_element.find('a', href=True)
            url = url_elem['href'] if url_elem else ""
            if url and not url.startswith('http'):
                url = self.base_url + url

            # Společnost
            spolecnost_elem = job_element.find('span', class_='companyName')
            spolecnost = spolecnost_elem.get_text(strip=True) if spolecnost_elem else "N/A"

            # Lokace
            lokace_elem = job_element.find('div', class_='companyLocation')
            lokace = lokace_elem.get_text(strip=True) if lokace_elem else "N/A"

            # Mzda
            mzda_elem = job_element.find('div', class_='salary-snippet')
            if not mzda_elem:
                mzda_elem = job_element.find('span', class_='salary-snippet-container')

            mzda = mzda_elem.get_text(strip=True) if mzda_elem else None

            # Typ úvazku
            typ_elem = job_element.find('div', class_='metadata')
            typ_uvazku = typ_elem.get_text(strip=True) if typ_elem else "N/A"

            job_data = {
                'nazev_pozice': nazev_pozice,
                'spolecnost': spolecnost,
                'lokace': lokace,
                'typ_uvazku': typ_uvazku,
                'url': url,
                'mzda': mzda,
                'portal': 'indeed.cz',
                'datum_nalezeni': datetime.now().strftime('%Y-%m-%d'),
            }

            return job_data

        except Exception as e:
            self.logger.error(f"Chyba při parsování job elementu: {e}", exc_info=True)
            return None
