"""
Konfigurace pro job scraper
Obsahuje klíčová slova, profil kandidáta a nastavení scraperu
"""

import os
from typing import List, Dict

# ============================================================================
# KLÍČOVÁ SLOVA PRO VYHLEDÁVÁNÍ
# ============================================================================

# Primární klíčová slova (povinné)
PRIMARY_KEYWORDS = [
    "projektový manažer",
    "project manager",
    "provozní manažer",
    "operations manager",
    "IT konzultant",
    "IT consultant",
    "IT manažer",
    "IT manager",
    "e-commerce manažer",
    "ecommerce manager",
]

# Sekundární klíčová slova (relevantní pro kandidátův profil)
SECONDARY_KEYWORDS = [
    "technical project manager",
    "delivery manager",
    "product owner",
    "implementation manager",
    "digital project manager",
    "senior project manager",
    "team lead",
    "business analyst",
    "Shopify manager",
    "Shoptet specialista",
    "ERP implementation manager",
]

# Všechna klíčová slova dohromady
ALL_KEYWORDS = PRIMARY_KEYWORDS + SECONDARY_KEYWORDS

# Klíčová slova k vyloučení (negativní filtr)
EXCLUDE_KEYWORDS = [
    "junior",
    "junior.",
    "mladší",
    "trainee",
    "intern",
    "internship",
    "stáž",
    "stážista",
]

# Vyloučené jazykové požadavky (v popisu/požadavcích)
# Pokud nabídka obsahuje některé z těchto frází, bude vyloučena
EXCLUDE_LANGUAGE_REQUIREMENTS = [
    # Angličtina C1
    "c1 english",
    "english c1",
    "angličtina c1",
    "c1 angličtina",
    "anglický jazyk c1",
    "c1 level english",
    "english level c1",

    # Němčina (všechny úrovně)
    "němčina",
    "nemčina",
    "german",
    "deutsch",
    "německý jazyk",
    "nemecký jazyk",
    "německy",
    "nemecky",
]

# ============================================================================
# PROFIL KANDIDÁTA
# ============================================================================

CANDIDATE_PROFILE = {
    "pozice": "Seniorní projektový manažer",
    "zkušenosti_let": 5,
    "oblast": "e-commerce",
    "kompetence": [
        "řízení implementací e-commerce platforem",
        "Shoptet",
        "Shopify",
        "integrace ERP systémů",
        "vedení cross-funkčních týmů",
        "UX/UI",
        "analytika",
        "risk management",
        "plánování",
        "rozpočtování",
        "AI a automatizace",
    ],
    "klienti": ["Rituals", "Philips", "Caffe Imperial Dolce"],
    "lokace_preferovana": ["Praha", "remote", "hybrid"],
}

# Požadované lokality (striktní filtr) - pouze nabídky z těchto lokalit
# Prázdný seznam = žádné filtrování podle lokality
REQUIRED_LOCATIONS = [
    "praha",
    "hlavní město praha",
    "prague",
]

# Klíčová slova pro vysokou relevanci (weighted scoring)
HIGH_RELEVANCE_KEYWORDS = [
    "e-commerce",
    "shopify",
    "shoptet",
    "erp",
    "implementace",
    "senior",
    "remote",
    "praha",
    "projektový",
    "project manager",
]

# ============================================================================
# NASTAVENÍ CÍLOVÝCH PORTÁLŮ
# ============================================================================

TARGET_PORTALS = {
    "jobs_cz": {
        "enabled": True,
        "base_url": "https://www.jobs.cz",
        "priority": 1,
    },
    "prace_cz": {
        "enabled": True,
        "base_url": "https://www.prace.cz",
        "priority": 2,
    },
    "startupjobs": {
        "enabled": True,
        "base_url": "https://www.startupjobs.cz",
        "priority": 3,
    },
    "linkedin": {
        "enabled": True,
        "base_url": "https://www.linkedin.com/jobs",
        "priority": 4,
        "region": "Czech Republic",
        "requires_auth": True,
    },
    "indeed": {
        "enabled": True,
        "base_url": "https://cz.indeed.com",
        "priority": 5,
    },
    "profesia": {
        "enabled": True,
        "base_url": "https://www.profesia.cz",
        "priority": 6,
    },
}

# ============================================================================
# TECHNICKÁ KONFIGURACE
# ============================================================================

# Rate limiting
REQUEST_DELAY_MIN = 2  # minimální delay mezi požadavky (sekundy)
REQUEST_DELAY_MAX = 5  # maximální delay mezi požadavky (sekundy)
MAX_RETRIES = 3  # počet pokusů při selhání
RETRY_BACKOFF = 2  # exponenciální backoff multiplikátor

# User-Agent rotace
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Timeouts
REQUEST_TIMEOUT = 30  # timeout pro HTTP požadavky (sekundy)

# ============================================================================
# VÝSTUPNÍ SOUBORY A LOGOVÁNÍ
# ============================================================================

# Excel výstup
EXCEL_OUTPUT_FILE = "job_listings.xlsx"
EXCEL_SHEET_NAME = "Nabídky"

# Logování
LOG_FILE = "scraper.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# SCHEDULING
# ============================================================================

# Denní běh v 8:00 ráno
SCHEDULE_TIME = "08:00"
SCHEDULE_ENABLED = False  # True pro daemon režim

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

# LinkedIn credentials (pokud je potřeba autentizace)
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

# Proxy nastavení (volitelné)
HTTP_PROXY = os.getenv("HTTP_PROXY", "")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "")

# ============================================================================
# STRUKTURA DAT PRO EXCEL
# ============================================================================

EXCEL_COLUMNS = [
    "ID",
    "Datum nalezení",
    "Název pozice",
    "Společnost",
    "Lokace",
    "Typ úvazku",
    "Portál",
    "URL",
    "Mzda",
    "Relevance",
    "Status",
    "Poznámky",
]

# Výchozí hodnoty
DEFAULT_STATUS = "New"
DEFAULT_RELEVANCE = "Medium"
