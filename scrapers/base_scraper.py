"""
Abstraktní základní třída pro všechny scrapery
Definuje společné rozhraní a funkcionalitu
"""

from abc import ABC, abstractmethod
import logging
import time
import random
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class BaseScraper(ABC):
    """
    Abstraktní třída pro scrapery pracovních portálů

    Poskytuje:
    - HTTP request handling s retry logikou
    - Rate limiting
    - User-Agent rotace
    - Error handling a logging
    - Společné rozhraní pro všechny scrapery
    """

    def __init__(self, portal_name: str):
        """
        Inicializace scraperu

        Args:
            portal_name: Název portálu (např. "jobs_cz")
        """
        self.portal_name = portal_name
        self.logger = logging.getLogger(f"scraper.{portal_name}")
        self.session = requests.Session()

        # Nastavení proxy pokud je definováno
        if config.HTTP_PROXY or config.HTTPS_PROXY:
            self.session.proxies = {
                'http': config.HTTP_PROXY,
                'https': config.HTTPS_PROXY,
            }

    def _get_random_user_agent(self) -> str:
        """Vrátí náhodný User-Agent header"""
        return random.choice(config.USER_AGENTS)

    def _random_delay(self):
        """Přidá náhodný delay mezi požadavky (rate limiting)"""
        delay = random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX)
        self.logger.debug(f"Čekám {delay:.2f} sekund před dalším požadavkem")
        time.sleep(delay)

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """
        Provede HTTP požadavek s retry logikou a error handlingem

        Args:
            url: URL adresa
            method: HTTP metoda (GET, POST, ...)
            **kwargs: Další parametry pro requests

        Returns:
            Response objekt nebo None při selhání
        """
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = self._get_random_user_agent()

        for attempt in range(config.MAX_RETRIES):
            try:
                self.logger.debug(f"Požadavek na {url} (pokus {attempt + 1}/{config.MAX_RETRIES})")

                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=config.REQUEST_TIMEOUT,
                    **kwargs
                )

                response.raise_for_status()

                # Rate limiting
                self._random_delay()

                return response

            except requests.exceptions.HTTPError as e:
                self.logger.warning(f"HTTP error při požadavku na {url}: {e}")
                if response.status_code == 429:  # Too Many Requests
                    wait_time = config.RETRY_BACKOFF ** (attempt + 2)
                    self.logger.warning(f"Rate limit detected, čekám {wait_time} sekund")
                    time.sleep(wait_time)
                elif response.status_code >= 500:  # Server error
                    wait_time = config.RETRY_BACKOFF ** attempt
                    time.sleep(wait_time)
                else:
                    # Client error (4xx) - neměl by se opakovat
                    self.logger.error(f"Client error {response.status_code}: {url}")
                    return None

            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout při požadavku na {url}")
                wait_time = config.RETRY_BACKOFF ** attempt
                time.sleep(wait_time)

            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error při požadavku na {url}: {e}")
                wait_time = config.RETRY_BACKOFF ** attempt
                time.sleep(wait_time)

            except Exception as e:
                self.logger.error(f"Neočekávaná chyba při požadavku na {url}: {e}", exc_info=True)
                return None

        self.logger.error(f"Všechny pokusy selhaly pro {url}")
        return None

    def _parse_html(self, html_content: str) -> Optional[BeautifulSoup]:
        """
        Naparsuje HTML obsah pomocí BeautifulSoup

        Args:
            html_content: HTML string

        Returns:
            BeautifulSoup objekt nebo None při chybě
        """
        try:
            return BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Chyba při parsování HTML: {e}", exc_info=True)
            return None

    @abstractmethod
    def scrape(self, keywords: List[str]) -> List[Dict]:
        """
        Hlavní metoda pro scraping - musí být implementována v potomcích

        Args:
            keywords: Seznam klíčových slov pro vyhledávání

        Returns:
            Seznam slovníků s informacemi o pracovních nabídkách

        Každý slovník by měl obsahovat:
        {
            'nazev_pozice': str,
            'spolecnost': str,
            'lokace': str,
            'typ_uvazku': str,  # Plný/částečný/remote
            'url': str,
            'mzda': str,  # nebo None
            'portal': str,
            'datum_nalezeni': str,  # YYYY-MM-DD
        }
        """
        pass

    @abstractmethod
    def _build_search_url(self, keyword: str) -> str:
        """
        Sestaví search URL pro daný portál a klíčové slovo

        Args:
            keyword: Klíčové slovo pro vyhledávání

        Returns:
            URL string pro vyhledávání
        """
        pass

    def _extract_job_details(self, job_element) -> Optional[Dict]:
        """
        Extrahuje detaily o pracovní nabídce z HTML elementu
        Může být přepsána v potomcích pro specifické potřeby

        Args:
            job_element: BeautifulSoup element obsahující info o nabídce

        Returns:
            Slovník s detaily nebo None
        """
        # Defaultní implementace - měla by být přepsána
        return None

    def get_portal_name(self) -> str:
        """Vrátí název portálu"""
        return self.portal_name
