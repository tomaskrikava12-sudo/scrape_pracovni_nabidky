"""
Scraper pro startupjobs.cz
Vyhledává pracovní nabídky na startupjobs.cz

DŮLEŽITÉ: StartupJobs používá JavaScript SPA (Nuxt.js).
HTML scraping nefunguje, protože obsah se načítá dynamicky.
Tento scraper používá interní API pro získání nabídek.
"""

from datetime import datetime
from typing import List, Dict, Optional
import urllib.parse
import json

from .base_scraper import BaseScraper

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class StartupJobsScraper(BaseScraper):
    """
    Scraper pro startupjobs.cz

    Používá interní API pro získání nabídek, protože web je
    JavaScript SPA a HTML scraping nefunguje.
    """

    # API endpoint pro vyhledávání nabídek
    API_BASE_URL = "https://api.startupjobs.cz/api"
    SEARCH_API_URL = "https://www.startupjobs.cz/api/offers"

    def __init__(self):
        """Inicializace startupjobs.cz scraperu"""
        super().__init__("startupjobs")
        self.base_url = config.TARGET_PORTALS["startupjobs"]["base_url"]

    def _build_search_url(self, keyword: str) -> str:
        """Sestaví search URL pro startupjobs.cz"""
        encoded_keyword = urllib.parse.quote_plus(keyword)
        return f"{self.base_url}/nabidky?search={encoded_keyword}"

    def _build_api_url(self, keyword: str, page: int = 1) -> str:
        """
        Sestaví API URL pro vyhledávání nabídek.

        Args:
            keyword: Klíčové slovo pro vyhledávání
            page: Číslo stránky

        Returns:
            API URL
        """
        params = {
            'search': keyword,
            'page': page,
            'limit': 50,
        }
        query_string = urllib.parse.urlencode(params)
        return f"{self.SEARCH_API_URL}?{query_string}"

    def scrape(self, keywords: List[str]) -> List[Dict]:
        """
        Scrapuje startupjobs.cz pro zadaná klíčová slova pomocí API.

        Args:
            keywords: Seznam klíčových slov pro vyhledávání

        Returns:
            Seznam nalezených pracovních nabídek
        """
        all_jobs = []
        self.logger.info(f"Začínám scraping startupjobs.cz s {len(keywords)} klíčovými slovy")

        for keyword in keywords:
            self.logger.info(f"Hledám: {keyword}")

            # Zkusíme API
            jobs = self._fetch_jobs_from_api(keyword)

            if jobs:
                all_jobs.extend(jobs)
                self.logger.info(f"Nalezeno {len(jobs)} nabídek pro '{keyword}'")
            else:
                self.logger.warning(f"Nepodařilo se získat výsledky pro '{keyword}'")

        # Odstranění duplicit podle URL
        unique_jobs = self._deduplicate_jobs(all_jobs)

        self.logger.info(f"Celkem nalezeno {len(unique_jobs)} unikátních nabídek na startupjobs.cz")
        return unique_jobs

    def _fetch_jobs_from_api(self, keyword: str) -> List[Dict]:
        """
        Získá nabídky z API.

        Args:
            keyword: Klíčové slovo pro vyhledávání

        Returns:
            Seznam nabídek
        """
        jobs = []

        # Zkusíme různé API formáty
        api_urls = [
            # Hlavní API endpoint
            f"https://www.startupjobs.cz/api/offers?search={urllib.parse.quote_plus(keyword)}",
            # Alternativní endpoint
            f"https://api.startupjobs.cz/api/offers?search={urllib.parse.quote_plus(keyword)}",
            # GraphQL-like endpoint
            f"https://www.startupjobs.cz/_nuxt/data/offers?search={urllib.parse.quote_plus(keyword)}",
        ]

        for api_url in api_urls:
            self.logger.debug(f"Zkouším API: {api_url}")

            try:
                response = self._make_request(api_url)
                if response and response.status_code == 200:
                    jobs = self._parse_api_response(response, keyword)
                    if jobs:
                        self.logger.debug(f"API {api_url} vrátilo {len(jobs)} nabídek")
                        return jobs
            except Exception as e:
                self.logger.debug(f"API {api_url} selhalo: {e}")
                continue

        # Fallback - zkusíme parsovat Nuxt data z HTML
        jobs = self._fetch_from_nuxt_data(keyword)

        return jobs

    def _parse_api_response(self, response, keyword: str) -> List[Dict]:
        """
        Parsuje JSON odpověď z API.

        Args:
            response: HTTP response objekt
            keyword: Hledané klíčové slovo

        Returns:
            Seznam nabídek
        """
        jobs = []

        try:
            data = response.json()

            # Různé formáty API odpovědí
            offers = []
            if isinstance(data, list):
                offers = data
            elif isinstance(data, dict):
                offers = data.get('data', []) or data.get('offers', []) or data.get('items', []) or data.get('results', [])

            for offer in offers:
                job = self._parse_offer(offer)
                if job:
                    jobs.append(job)

        except json.JSONDecodeError as e:
            self.logger.debug(f"Nepodařilo se parsovat JSON: {e}")
        except Exception as e:
            self.logger.debug(f"Chyba při parsování API odpovědi: {e}")

        return jobs

    def _parse_offer(self, offer: Dict) -> Optional[Dict]:
        """
        Parsuje jednotlivou nabídku z API.

        Args:
            offer: Slovník s daty nabídky z API

        Returns:
            Standardizovaný slovník nabídky
        """
        try:
            # Název pozice - různé možné klíče
            nazev_pozice = (
                offer.get('name') or
                offer.get('title') or
                offer.get('position') or
                offer.get('nazev') or
                offer.get('jobTitle') or
                "N/A"
            )

            if nazev_pozice == "N/A":
                return None

            # Společnost
            company_data = offer.get('company') or offer.get('startup') or {}
            if isinstance(company_data, dict):
                spolecnost = company_data.get('name') or company_data.get('title') or "N/A"
            else:
                spolecnost = str(company_data) if company_data else "N/A"

            # Lokace
            locations = offer.get('locations') or offer.get('location') or []
            if isinstance(locations, list):
                lokace = ", ".join([
                    loc.get('name') or loc.get('city') or str(loc)
                    for loc in locations if loc
                ]) or "N/A"
            elif isinstance(locations, dict):
                lokace = locations.get('name') or locations.get('city') or "N/A"
            else:
                lokace = str(locations) if locations else "N/A"

            # URL nabídky
            url = offer.get('url') or offer.get('link') or ""
            if not url and offer.get('slug'):
                url = f"{self.base_url}/nabidka/{offer.get('slug')}"
            elif not url and offer.get('id'):
                url = f"{self.base_url}/nabidka/{offer.get('id')}"

            if url and not url.startswith('http'):
                url = self.base_url + url

            # Mzda
            salary_data = offer.get('salary') or offer.get('mzda') or {}
            if isinstance(salary_data, dict):
                mzda_min = salary_data.get('min') or salary_data.get('from') or ""
                mzda_max = salary_data.get('max') or salary_data.get('to') or ""
                currency = salary_data.get('currency', 'CZK')
                if mzda_min and mzda_max:
                    mzda = f"{mzda_min} - {mzda_max} {currency}"
                elif mzda_min:
                    mzda = f"od {mzda_min} {currency}"
                elif mzda_max:
                    mzda = f"do {mzda_max} {currency}"
                else:
                    mzda = None
            elif salary_data:
                mzda = str(salary_data)
            else:
                mzda = None

            # Typ úvazku
            employment_types = offer.get('employmentTypes') or offer.get('employment_type') or []
            if isinstance(employment_types, list):
                typ_uvazku = ", ".join([
                    et.get('name') or str(et)
                    for et in employment_types if et
                ]) or "N/A"
            else:
                typ_uvazku = str(employment_types) if employment_types else "N/A"

            # Popis
            popis = offer.get('description') or offer.get('perex') or offer.get('summary') or ""

            return {
                'nazev_pozice': nazev_pozice,
                'spolecnost': spolecnost,
                'lokace': lokace,
                'typ_uvazku': typ_uvazku,
                'url': url,
                'mzda': mzda,
                'popis': popis[:500] if popis else "",  # Omezíme délku popisu
                'portal': 'startupjobs.cz',
                'datum_nalezeni': datetime.now().strftime('%Y-%m-%d'),
            }

        except Exception as e:
            self.logger.debug(f"Chyba při parsování nabídky: {e}")
            return None

    def _fetch_from_nuxt_data(self, keyword: str) -> List[Dict]:
        """
        Zkusí získat data z Nuxt.js __NUXT_DATA__ v HTML.

        StartupJobs používá Nuxt.js, které vkládá data do HTML.
        Toto je fallback pokud API nefunguje.

        Args:
            keyword: Klíčové slovo

        Returns:
            Seznam nabídek
        """
        jobs = []

        search_url = self._build_search_url(keyword)
        self.logger.debug(f"Zkouším Nuxt data z: {search_url}")

        response = self._make_request(search_url)
        if not response:
            return jobs

        try:
            # Hledáme __NUXT_DATA__ script tag
            soup = self._parse_html(response.text)
            if not soup:
                return jobs

            nuxt_data_script = soup.find('script', {'id': '__NUXT_DATA__'})
            if nuxt_data_script and nuxt_data_script.string:
                # Nuxt 3 používá speciální formát dat
                nuxt_text = nuxt_data_script.string
                self.logger.debug(f"Nalezen __NUXT_DATA__ script ({len(nuxt_text)} znaků)")

                # Zkusíme parsovat jako JSON array
                try:
                    nuxt_array = json.loads(nuxt_text)
                    # Hledáme objekty s nabídkami v poli
                    jobs = self._extract_jobs_from_nuxt_array(nuxt_array)
                except json.JSONDecodeError:
                    self.logger.debug("Nepodařilo se parsovat Nuxt data jako JSON")

        except Exception as e:
            self.logger.debug(f"Chyba při parsování Nuxt dat: {e}")

        return jobs

    def _extract_jobs_from_nuxt_array(self, nuxt_array: list) -> List[Dict]:
        """
        Extrahuje nabídky z Nuxt.js data array.

        Args:
            nuxt_array: Pole dat z __NUXT_DATA__

        Returns:
            Seznam nabídek
        """
        jobs = []

        # Nuxt 3 data jsou pole referencí, hledáme objekty vypadající jako nabídky
        for item in nuxt_array:
            if isinstance(item, dict):
                # Hledáme objekty s klíči typickými pro nabídky
                if any(key in item for key in ['name', 'title', 'slug', 'company', 'locations']):
                    job = self._parse_offer(item)
                    if job:
                        jobs.append(job)

        return jobs

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Odstraní duplicitní nabídky podle URL.

        Args:
            jobs: Seznam nabídek

        Returns:
            Seznam unikátních nabídek
        """
        seen_urls = set()
        unique_jobs = []

        for job in jobs:
            url = job.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
            elif not url:
                # Nabídky bez URL - použijeme hash z názvu a společnosti
                job_hash = f"{job.get('nazev_pozice')}|{job.get('spolecnost')}"
                if job_hash not in seen_urls:
                    seen_urls.add(job_hash)
                    unique_jobs.append(job)

        return unique_jobs
