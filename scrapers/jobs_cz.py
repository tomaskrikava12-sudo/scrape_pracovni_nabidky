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
        """
        jobs = []

        # Aktuální selektory podle HTML struktury jobs.cz (leden 2024)
        # Hledáme hlavní kontejner s nabídkami
        job_listings = soup.find_all('article', class_=lambda x: x and 'SearchResultCard' in x)

        if not job_listings:
            # Zkusit alternativní selektor
            job_listings = soup.find_all('div', class_=lambda x: x and 'SearchResultCard' in x)

        if not job_listings:
            self.logger.warning("Nenalezeny žádné job listings (možná změna HTML struktury)")
            self.logger.debug(f"HTML snippet: {str(soup)[:500]}")
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
            job_element: BeautifulSoup element (SearchResultCard)

        Returns:
            Slovník s daty nebo None
        """
        try:
            # Název pozice a URL - z linku v h2
            title_link = job_element.find('a', class_=lambda x: x and 'SearchResultCard__titleLink' in x)

            if not title_link:
                # Fallback - zkusit najít jakýkoliv link
                title_link = job_element.find('a', href=True)

            if title_link:
                nazev_pozice = title_link.get_text(strip=True)
                url = title_link.get('href', '')
                if url and not url.startswith('http'):
                    url = self.base_url + url
            else:
                nazev_pozice = "N/A"
                url = ""

            # Společnost - hledáme v metadata nebo info sekcích
            spolecnost_elem = job_element.find('a', class_=lambda x: x and 'SearchResultCard__org' in x)
            if not spolecnost_elem:
                spolecnost_elem = job_element.find(class_=lambda x: x and 'employer' in str(x).lower())
            if not spolecnost_elem:
                spolecnost_elem = job_element.find(class_=lambda x: x and 'company' in str(x).lower())

            spolecnost = spolecnost_elem.get_text(strip=True) if spolecnost_elem else "N/A"

            # Lokace
            lokace_elem = job_element.find('span', class_=lambda x: x and 'SearchResultCard__location' in x)
            if not lokace_elem:
                lokace_elem = job_element.find(class_=lambda x: x and 'locality' in str(x).lower())
            if not lokace_elem:
                lokace_elem = job_element.find(class_=lambda x: x and 'location' in str(x).lower())

            lokace = lokace_elem.get_text(strip=True) if lokace_elem else "N/A"

            # Mzda (není vždy uvedena)
            mzda_elem = job_element.find(class_=lambda x: x and 'salary' in str(x).lower())
            if not mzda_elem:
                mzda_elem = job_element.find(class_=lambda x: x and 'wage' in str(x).lower())

            mzda = mzda_elem.get_text(strip=True) if mzda_elem else None

            # Typ úvazku
            typ_elem = job_element.find(class_=lambda x: x and ('employment' in str(x).lower() or 'contract' in str(x).lower()))
            typ_uvazku = typ_elem.get_text(strip=True) if typ_elem else "N/A"

            # Popis/požadavky nabídky (pro filtrování jazyků apod.)
            popis_elem = job_element.find(class_=lambda x: x and 'description' in str(x).lower())
            if not popis_elem:
                popis_elem = job_element.find(class_=lambda x: x and 'requirements' in str(x).lower())
            if not popis_elem:
                popis_elem = job_element.find(class_=lambda x: x and 'SearchResultCard__label' in str(x))

            popis = popis_elem.get_text(strip=True) if popis_elem else ""

            # Sestavení výsledku
            job_data = {
                'nazev_pozice': nazev_pozice,
                'spolecnost': spolecnost,
                'lokace': lokace,
                'typ_uvazku': typ_uvazku,
                'url': url,
                'mzda': mzda,
                'popis': popis,  # Přidán popis pro filtrování
                'portal': 'jobs.cz',
                'datum_nalezeni': datetime.now().strftime('%Y-%m-%d'),
            }

            return job_data

        except Exception as e:
            self.logger.error(f"Chyba při parsování job elementu: {e}", exc_info=True)
            return None
