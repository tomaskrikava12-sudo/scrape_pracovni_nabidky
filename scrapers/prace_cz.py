"""
Scraper pro prace.cz
Vyhledává pracovní nabídky na prace.cz
"""

from datetime import datetime
from typing import List, Dict
import urllib.parse
import unicodedata

from .base_scraper import BaseScraper

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class PraceCzScraper(BaseScraper):
    """
    Scraper pro prace.cz

    POZNÁMKA: HTML selektory jsou podle skutečné struktury prace.cz
    """

    def __init__(self):
        """Inicializace prace.cz scraperu"""
        super().__init__("prace_cz")
        self.base_url = config.TARGET_PORTALS["prace_cz"]["base_url"]

    def _normalize_keyword(self, keyword: str) -> str:
        """
        Normalizuje keyword pro prace.cz URL formát

        Převádí "Projektový manažer" → "projektovy-manazer"
        """
        # Odstranění diakritiky
        normalized = unicodedata.normalize('NFKD', keyword)
        ascii_keyword = ''.join([c for c in normalized if not unicodedata.combining(c)])

        # Lowercase a nahrazení mezer pomlčkami
        slug = ascii_keyword.lower().replace(' ', '-')

        # Odstranění speciálních znaků kromě pomlček
        slug = ''.join([c if c.isalnum() or c == '-' else '' for c in slug])

        # Odstranění duplicitních pomlček
        while '--' in slug:
            slug = slug.replace('--', '-')

        # Odstranění pomlček na začátku/konci
        slug = slug.strip('-')

        return slug

    def _build_search_url(self, keyword: str) -> str:
        """Sestaví search URL pro prace.cz"""
        normalized_keyword = self._normalize_keyword(keyword)
        url = f"{self.base_url}/nabidky/{normalized_keyword}/"
        self.logger.debug(f"URL pro '{keyword}': {url}")
        return url

    def scrape(self, keywords: List[str]) -> List[Dict]:
        """Scrapuje prace.cz pro zadaná klíčová slova"""
        all_jobs = []
        self.logger.info(f"Začínám scraping prace.cz s {len(keywords)} klíčovými slovy")

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

        self.logger.info(f"Celkem nalezeno {len(all_jobs)} nabídek na prace.cz")
        return all_jobs

    def _extract_jobs_from_page(self, soup, keyword: str) -> List[Dict]:
        """Extrahuje nabídky ze stránky s výsledky"""
        jobs = []

        # Skutečné selektory podle HTML struktury prace.cz
        job_listings = soup.find_all('li', class_='search-result__advert')

        if not job_listings:
            self.logger.warning("Nenalezeny žádné job listings")
            return jobs

        self.logger.debug(f"Nalezeno {len(job_listings)} job listings")

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
            self.logger.debug("=== Začínám parsování nabídky prace.cz ===")

            # Název pozice - v h3.half-standalone → a → strong
            nazev_pozice = "N/A"
            h3_elem = job_element.find('h3', class_='half-standalone')
            if h3_elem:
                a_elem = h3_elem.find('a', class_='link')
                if a_elem:
                    strong_elem = a_elem.find('strong')
                    if strong_elem:
                        nazev_pozice = strong_elem.get_text(strip=True)
                    else:
                        nazev_pozice = a_elem.get_text(strip=True)

            self.logger.debug(f"Název: {nazev_pozice}")

            # URL - také v h3 → a[href]
            url = ""
            if h3_elem:
                a_elem = h3_elem.find('a', href=True)
                if a_elem:
                    url = a_elem['href']
                    if url and not url.startswith('http'):
                        url = self.base_url + url

            self.logger.debug(f"URL: {url}")

            # Lokace - div.search-result__advert__box__item--location → strong
            lokace = "N/A"
            lokace_div = job_element.find('div', class_='search-result__advert__box__item--location')
            if lokace_div:
                strong_elem = lokace_div.find('strong')
                if strong_elem:
                    lokace = strong_elem.get_text(strip=True)
                else:
                    lokace = lokace_div.get_text(strip=True)

            self.logger.debug(f"Lokace: {lokace}")

            # Společnost - div.search-result__advert__box__item--company
            spolecnost = "N/A"
            company_div = job_element.find('div', class_='search-result__advert__box__item--company')
            if company_div:
                # Odstraníme oddělovač •
                separator = company_div.find('div', class_='search-result__advert__box__separator')
                if separator:
                    separator.decompose()
                spolecnost = company_div.get_text(strip=True)

            self.logger.debug(f"Společnost: {spolecnost}")

            # Typ úvazku - div.search-result__advert__box__item--employment-type
            typ_uvazku = "N/A"
            type_div = job_element.find('div', class_='search-result__advert__box__item--employment-type')
            if type_div:
                # Odstraníme oddělovač •
                separator = type_div.find('div', class_='search-result__advert__box__separator')
                if separator:
                    separator.decompose()
                typ_uvazku = type_div.get_text(strip=True)

            self.logger.debug(f"Typ úvazku: {typ_uvazku}")

            # Mzda - hledáme div s třídou obsahující 'salary' nebo 'wage'
            mzda = None
            salary_div = job_element.find('div', class_=lambda x: x and ('salary' in x or 'wage' in x))
            if salary_div:
                mzda = salary_div.get_text(strip=True)

            self.logger.debug(f"Mzda: {mzda}")

            job_data = {
                'nazev_pozice': nazev_pozice,
                'spolecnost': spolecnost,
                'lokace': lokace,
                'typ_uvazku': typ_uvazku,
                'url': url,
                'mzda': mzda,
                'portal': 'prace.cz',
                'datum_nalezeni': datetime.now().strftime('%Y-%m-%d'),
            }

            return job_data

        except Exception as e:
            self.logger.error(f"Chyba při parsování job elementu: {e}", exc_info=True)
            return None
