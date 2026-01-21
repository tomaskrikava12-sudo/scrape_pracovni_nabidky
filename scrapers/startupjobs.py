"""
Scraper pro startupjobs.cz
Vyhledává pracovní nabídky na startupjobs.cz

POZNÁMKA: HTML selektory jsou odvozeny z běžných vzorů job boardů.
Pokud scraper nenajde nabídky, spusťte s DEBUG logováním
a zkontrolujte skutečnou HTML strukturu ve výstupu.
"""

from datetime import datetime
from typing import List, Dict, Optional
import urllib.parse
import re

from .base_scraper import BaseScraper

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class StartupJobsScraper(BaseScraper):
    """
    Scraper pro startupjobs.cz

    Implementuje robustní extrakci s více fallback selektory
    pro lepší odolnost proti změnám HTML struktury.
    """

    # Selektory pro kontejner nabídek (v pořadí priority)
    JOB_CONTAINER_SELECTORS = [
        # Běžné vzory pro job karty
        ('div', {'class_': re.compile(r'job[-_]?card', re.I)}),
        ('div', {'class_': re.compile(r'job[-_]?offer', re.I)}),
        ('div', {'class_': re.compile(r'offer[-_]?card', re.I)}),
        ('div', {'class_': re.compile(r'position[-_]?card', re.I)}),
        ('article', {'class_': re.compile(r'job', re.I)}),
        ('article', {'class_': re.compile(r'offer', re.I)}),
        ('li', {'class_': re.compile(r'job', re.I)}),
        ('a', {'class_': re.compile(r'job[-_]?card', re.I)}),
        # Data atributy
        ('div', {'attrs': {'data-job-id': True}}),
        ('div', {'attrs': {'data-offer-id': True}}),
        ('article', {'attrs': {'data-jobid': True}}),
    ]

    # Selektory pro název pozice
    TITLE_SELECTORS = [
        ('h2', {'class_': re.compile(r'title|name|position', re.I)}),
        ('h3', {'class_': re.compile(r'title|name|position', re.I)}),
        ('a', {'class_': re.compile(r'title|name', re.I)}),
        ('span', {'class_': re.compile(r'title|name|position', re.I)}),
        ('div', {'class_': re.compile(r'job[-_]?title', re.I)}),
        ('h2', {}),  # Fallback na první h2
        ('h3', {}),  # Fallback na první h3
    ]

    # Selektory pro společnost
    COMPANY_SELECTORS = [
        ('div', {'class_': re.compile(r'company|startup|firm', re.I)}),
        ('span', {'class_': re.compile(r'company|startup|firm', re.I)}),
        ('a', {'class_': re.compile(r'company|startup', re.I)}),
        ('p', {'class_': re.compile(r'company', re.I)}),
        ('strong', {'class_': re.compile(r'company', re.I)}),
    ]

    # Selektory pro lokaci
    LOCATION_SELECTORS = [
        ('span', {'class_': re.compile(r'location|place|city|lokal', re.I)}),
        ('div', {'class_': re.compile(r'location|place|city', re.I)}),
        ('p', {'class_': re.compile(r'location', re.I)}),
        ('a', {'class_': re.compile(r'location', re.I)}),
    ]

    # Selektory pro mzdu
    SALARY_SELECTORS = [
        ('span', {'class_': re.compile(r'salary|wage|pay|mzda|plat', re.I)}),
        ('div', {'class_': re.compile(r'salary|wage|pay|mzda', re.I)}),
        ('p', {'class_': re.compile(r'salary', re.I)}),
    ]

    # Selektory pro typ úvazku
    JOB_TYPE_SELECTORS = [
        ('span', {'class_': re.compile(r'type|contract|uvazek|employment', re.I)}),
        ('div', {'class_': re.compile(r'type|contract|employment', re.I)}),
        ('span', {'class_': re.compile(r'tag|label|badge', re.I)}),
    ]

    def __init__(self):
        """Inicializace startupjobs.cz scraperu"""
        super().__init__("startupjobs")
        self.base_url = config.TARGET_PORTALS["startupjobs"]["base_url"]

    def _build_search_url(self, keyword: str) -> str:
        """Sestaví search URL pro startupjobs.cz"""
        encoded_keyword = urllib.parse.quote_plus(keyword)
        # Formát URL: /nabidky?search=keyword
        return f"{self.base_url}/nabidky?search={encoded_keyword}"

    def scrape(self, keywords: List[str]) -> List[Dict]:
        """
        Scrapuje startupjobs.cz pro zadaná klíčová slova

        Args:
            keywords: Seznam klíčových slov pro vyhledávání

        Returns:
            Seznam nalezených pracovních nabídek
        """
        all_jobs = []
        self.logger.info(f"Začínám scraping startupjobs.cz s {len(keywords)} klíčovými slovy")

        for keyword in keywords:
            self.logger.info(f"Hledám: {keyword}")
            search_url = self._build_search_url(keyword)
            self.logger.debug(f"URL: {search_url}")

            response = self._make_request(search_url)
            if not response:
                self.logger.warning(f"Nepodařilo se získat výsledky pro '{keyword}'")
                continue

            soup = self._parse_html(response.text)
            if not soup:
                continue

            # Debug: Zalogujeme základní strukturu stránky
            self._log_page_structure(soup)

            jobs = self._extract_jobs_from_page(soup, keyword)
            all_jobs.extend(jobs)

            self.logger.info(f"Nalezeno {len(jobs)} nabídek pro '{keyword}'")

        # Odstranění duplicit podle URL
        unique_jobs = self._deduplicate_jobs(all_jobs)

        self.logger.info(f"Celkem nalezeno {len(unique_jobs)} unikátních nabídek na startupjobs.cz")
        return unique_jobs

    def _log_page_structure(self, soup) -> None:
        """
        Zaloguje strukturu stránky pro debug účely.
        Pomáhá identifikovat správné selektory.
        """
        self.logger.debug("=== DEBUG: Analýza HTML struktury ===")

        # Najdi potenciální kontejnery nabídek
        for tag in ['article', 'div', 'li', 'a']:
            elements = soup.find_all(tag)
            classes = set()
            for el in elements[:50]:  # Omezíme na prvních 50
                if el.get('class'):
                    classes.update(el.get('class'))
            if classes:
                job_related = [c for c in classes if any(
                    kw in c.lower() for kw in ['job', 'offer', 'card', 'position', 'listing', 'result']
                )]
                if job_related:
                    self.logger.debug(f"<{tag}> třídy relevantní pro nabídky: {job_related}")

    def _find_job_containers(self, soup) -> List:
        """
        Najde kontejnery s nabídkami práce pomocí více fallback selektorů.

        Returns:
            Seznam BeautifulSoup elementů obsahujících nabídky
        """
        for tag, attrs in self.JOB_CONTAINER_SELECTORS:
            try:
                if 'class_' in attrs:
                    containers = soup.find_all(tag, class_=attrs['class_'])
                elif 'attrs' in attrs:
                    containers = soup.find_all(tag, attrs=attrs['attrs'])
                else:
                    containers = soup.find_all(tag, attrs)

                if containers and len(containers) > 0:
                    self.logger.debug(f"Nalezeny kontejnery pomocí: <{tag}> {attrs} - počet: {len(containers)}")
                    return containers
            except Exception as e:
                self.logger.debug(f"Selector <{tag}> {attrs} selhal: {e}")
                continue

        return []

    def _find_element_text(self, container, selectors: List, default: str = "N/A") -> str:
        """
        Najde text elementu pomocí seznamu selektorů.

        Args:
            container: BeautifulSoup element k prohledání
            selectors: Seznam (tag, attrs) tuples
            default: Výchozí hodnota pokud nenalezeno

        Returns:
            Nalezený text nebo default hodnota
        """
        for tag, attrs in selectors:
            try:
                if 'class_' in attrs:
                    element = container.find(tag, class_=attrs['class_'])
                else:
                    element = container.find(tag, attrs) if attrs else container.find(tag)

                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return text
            except Exception:
                continue

        return default

    def _extract_jobs_from_page(self, soup, keyword: str) -> List[Dict]:
        """
        Extrahuje nabídky ze stránky s výsledky.

        Args:
            soup: BeautifulSoup objekt stránky
            keyword: Hledané klíčové slovo

        Returns:
            Seznam slovníků s daty nabídek
        """
        jobs = []

        job_containers = self._find_job_containers(soup)

        if not job_containers:
            self.logger.warning("Nenalezeny žádné kontejnery s nabídkami")
            self.logger.debug("Zkuste zkontrolovat HTML strukturu a upravit selektory")
            # Debug: Uložíme část HTML pro analýzu
            self._save_debug_html(soup)
            return jobs

        self.logger.debug(f"Nalezeno {len(job_containers)} potenciálních nabídek")

        for job_elem in job_containers:
            try:
                job_data = self._extract_job_details(job_elem)
                if job_data and job_data.get('nazev_pozice') != "N/A":
                    jobs.append(job_data)
            except Exception as e:
                self.logger.error(f"Chyba při extrakci nabídky: {e}", exc_info=True)
                continue

        return jobs

    def _extract_job_details(self, job_element) -> Optional[Dict]:
        """
        Extrahuje detaily o nabídce z HTML elementu.

        Args:
            job_element: BeautifulSoup element s nabídkou

        Returns:
            Slovník s daty nabídky nebo None při chybě
        """
        try:
            # Název pozice
            nazev_pozice = self._find_element_text(job_element, self.TITLE_SELECTORS, "N/A")

            # URL nabídky
            url = self._extract_url(job_element)

            # Společnost
            spolecnost = self._find_element_text(job_element, self.COMPANY_SELECTORS, "N/A")

            # Lokace
            lokace = self._find_element_text(job_element, self.LOCATION_SELECTORS, "N/A")

            # Mzda
            mzda = self._find_element_text(job_element, self.SALARY_SELECTORS, None)
            if mzda == "N/A":
                mzda = None

            # Typ úvazku
            typ_uvazku = self._find_element_text(job_element, self.JOB_TYPE_SELECTORS, "N/A")

            # Popis - zkusíme najít kratký popis/perex
            popis = self._extract_description(job_element)

            job_data = {
                'nazev_pozice': nazev_pozice,
                'spolecnost': spolecnost,
                'lokace': lokace,
                'typ_uvazku': typ_uvazku,
                'url': url,
                'mzda': mzda,
                'popis': popis,
                'portal': 'startupjobs.cz',
                'datum_nalezeni': datetime.now().strftime('%Y-%m-%d'),
            }

            self.logger.debug(f"Extrahována nabídka: {nazev_pozice} @ {spolecnost}")
            return job_data

        except Exception as e:
            self.logger.error(f"Chyba při parsování job elementu: {e}", exc_info=True)
            return None

    def _extract_url(self, job_element) -> str:
        """
        Extrahuje URL nabídky.

        Args:
            job_element: BeautifulSoup element

        Returns:
            Absolutní URL nabídky
        """
        # Zkusíme najít odkaz
        url_elem = job_element.find('a', href=True)

        # Pokud je celý element odkaz
        if not url_elem and job_element.name == 'a' and job_element.get('href'):
            url_elem = job_element

        if url_elem:
            url = url_elem.get('href', '')
            # Normalizace URL
            if url and not url.startswith('http'):
                if url.startswith('/'):
                    url = self.base_url + url
                else:
                    url = self.base_url + '/' + url
            return url

        return ""

    def _extract_description(self, job_element) -> str:
        """
        Extrahuje krátký popis/perex nabídky.

        Args:
            job_element: BeautifulSoup element

        Returns:
            Text popisu nebo prázdný string
        """
        description_selectors = [
            ('p', {'class_': re.compile(r'desc|perex|summary|excerpt', re.I)}),
            ('div', {'class_': re.compile(r'desc|perex|summary', re.I)}),
            ('span', {'class_': re.compile(r'desc|perex', re.I)}),
            ('p', {}),  # Fallback na první odstavec
        ]

        return self._find_element_text(job_element, description_selectors, "")

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
                # Nabídky bez URL zachováme, ale logujeme
                self.logger.debug(f"Nabídka bez URL: {job.get('nazev_pozice')}")
                unique_jobs.append(job)

        return unique_jobs

    def _save_debug_html(self, soup) -> None:
        """
        Uloží část HTML pro debug analýzu.

        Args:
            soup: BeautifulSoup objekt
        """
        try:
            # Najdeme hlavní obsah stránky
            main_content = soup.find('main') or soup.find('div', {'id': 'content'}) or soup.find('body')
            if main_content:
                # Uložíme prvních 5000 znaků
                debug_html = str(main_content)[:5000]
                self.logger.debug(f"HTML struktura (prvních 5000 znaků):\n{debug_html}")
        except Exception as e:
            self.logger.debug(f"Nepodařilo se uložit debug HTML: {e}")
