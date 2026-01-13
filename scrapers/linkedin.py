"""
Scraper pro LinkedIn Jobs
Vyhledává pracovní nabídky na LinkedIn (region: Česká republika)
"""

from datetime import datetime
from typing import List, Dict
import urllib.parse

from .base_scraper import BaseScraper

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class LinkedInScraper(BaseScraper):
    """
    Scraper pro LinkedIn Jobs

    UPOZORNĚNÍ: LinkedIn často vyžaduje autentizaci pro scraping.
    Tento scraper může vyžadovat login nebo může být blokován.
    Doporučuje se použití LinkedIn API nebo Selenium pro autentizaci.

    POZNÁMKA: HTML selektory jsou ukázkové
    """

    def __init__(self):
        """Inicializace LinkedIn scraperu"""
        super().__init__("linkedin")
        self.base_url = config.TARGET_PORTALS["linkedin"]["base_url"]
        self.requires_auth = config.TARGET_PORTALS["linkedin"]["requires_auth"]

    def _build_search_url(self, keyword: str) -> str:
        """Sestaví search URL pro LinkedIn Jobs"""
        encoded_keyword = urllib.parse.quote_plus(keyword)
        # location=Czech%20Republic
        return f"{self.base_url}/search/?keywords={encoded_keyword}&location=Czech%20Republic"

    def scrape(self, keywords: List[str]) -> List[Dict]:
        """Scrapuje LinkedIn Jobs pro zadaná klíčová slova"""
        all_jobs = []
        self.logger.info(f"Začínám scraping LinkedIn s {len(keywords)} klíčovými slovy")

        if self.requires_auth and not (config.LINKEDIN_EMAIL and config.LINKEDIN_PASSWORD):
            self.logger.warning(
                "LinkedIn vyžaduje autentizaci, ale credentials nejsou nastaveny. "
                "Nastavte LINKEDIN_EMAIL a LINKEDIN_PASSWORD v environment variables."
            )
            # Pokračovat i bez autentizace - může fungovat pro veřejné výsledky
            # return all_jobs

        for keyword in keywords:
            self.logger.info(f"Hledám: {keyword}")
            search_url = self._build_search_url(keyword)

            response = self._make_request(search_url)
            if not response:
                self.logger.warning(f"Nepodařilo se získat výsledky pro '{keyword}' (možná vyžaduje login)")
                continue

            soup = self._parse_html(response.text)
            if not soup:
                continue

            # Kontrola, zda nás LinkedIn nepřesměroval na login
            if 'authwall' in response.url or 'login' in response.url:
                self.logger.warning("LinkedIn vyžaduje autentizaci - scraping přeskočen")
                break

            jobs = self._extract_jobs_from_page(soup, keyword)
            all_jobs.extend(jobs)

            self.logger.info(f"Nalezeno {len(jobs)} nabídek pro '{keyword}'")

        self.logger.info(f"Celkem nalezeno {len(all_jobs)} nabídek na LinkedIn")
        return all_jobs

    def _extract_jobs_from_page(self, soup, keyword: str) -> List[Dict]:
        """Extrahuje nabídky ze stránky s výsledky"""
        jobs = []

        # UKÁZKOVÉ selektory pro LinkedIn
        job_listings = soup.find_all('li', class_='jobs-search__results-list')

        if not job_listings:
            job_listings = soup.find_all('div', attrs={'data-job-id': True})

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
            nazev_elem = job_element.find('h3', class_='base-search-card__title')
            if not nazev_elem:
                nazev_elem = job_element.find('a', class_='job-card-list__title')

            nazev_pozice = nazev_elem.get_text(strip=True) if nazev_elem else "N/A"

            # URL
            url_elem = job_element.find('a', class_='base-card__full-link')
            url = url_elem['href'] if url_elem and url_elem.get('href') else ""

            # Společnost
            spolecnost_elem = job_element.find('h4', class_='base-search-card__subtitle')
            spolecnost = spolecnost_elem.get_text(strip=True) if spolecnost_elem else "N/A"

            # Lokace
            lokace_elem = job_element.find('span', class_='job-search-card__location')
            lokace = lokace_elem.get_text(strip=True) if lokace_elem else "N/A"

            # LinkedIn obvykle nezobrazuje mzdu ve výsledcích vyhledávání
            mzda = None

            # Typ úvazku
            typ_elem = job_element.find('span', class_='job-type')
            typ_uvazku = typ_elem.get_text(strip=True) if typ_elem else "N/A"

            job_data = {
                'nazev_pozice': nazev_pozice,
                'spolecnost': spolecnost,
                'lokace': lokace,
                'typ_uvazku': typ_uvazku,
                'url': url,
                'mzda': mzda,
                'portal': 'linkedin.com',
                'datum_nalezeni': datetime.now().strftime('%Y-%m-%d'),
            }

            return job_data

        except Exception as e:
            self.logger.error(f"Chyba při parsování job elementu: {e}", exc_info=True)
            return None
