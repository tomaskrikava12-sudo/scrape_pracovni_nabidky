#!/usr/bin/env python3
"""
Hlavní orchestrátor pro job scraper
Řídí průběh scrapování, deduplikaci a zápis do Excel souboru
"""

import logging
import argparse
import sys
from datetime import datetime
import schedule
import time

# Import scraperů
from scrapers.jobs_cz import JobsCzScraper
from scrapers.prace_cz import PraceCzScraper
from scrapers.startupjobs import StartupJobsScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.indeed import IndeedScraper
from scrapers.profesia import ProfesiaScraper

# Import utility modulů
from utils.deduplicator import Deduplicator
from utils.excel_handler import ExcelHandler
from utils.relevance import RelevanceScorer

import config


def setup_logging():
    """Nastavení loggingu"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def filter_by_location(jobs: list) -> list:
    """
    Filtruje nabídky podle požadované lokality

    Args:
        jobs: Seznam nabídek

    Returns:
        Filtrovaný seznam nabídek
    """
    if not config.REQUIRED_LOCATIONS:
        return jobs

    filtered_jobs = []
    for job in jobs:
        lokace = (job.get('lokace', '') or '').lower()

        # Kontrola zda lokace obsahuje některou z požadovaných lokalit
        if any(req_loc in lokace for req_loc in config.REQUIRED_LOCATIONS):
            filtered_jobs.append(job)

    return filtered_jobs


def filter_by_exclude_keywords(jobs: list) -> list:
    """
    Vyfiltruje nabídky obsahující nežádoucí klíčová slova (např. junior)

    Args:
        jobs: Seznam nabídek

    Returns:
        Filtrovaný seznam nabídek
    """
    if not config.EXCLUDE_KEYWORDS:
        return jobs

    filtered_jobs = []
    for job in jobs:
        nazev = (job.get('nazev_pozice', '') or '').lower()

        # Kontrola zda název obsahuje nějaké vyloučené klíčové slovo
        if not any(exclude_kw in nazev for exclude_kw in config.EXCLUDE_KEYWORDS):
            filtered_jobs.append(job)

    return filtered_jobs


def filter_by_language_requirements(jobs: list) -> list:
    """
    Vyfiltruje nabídky s nežádoucími jazykovými požadavky (C1 angličtina, němčina)

    Args:
        jobs: Seznam nabídek

    Returns:
        Filtrovaný seznam nabídek
    """
    if not config.EXCLUDE_LANGUAGE_REQUIREMENTS:
        return jobs

    filtered_jobs = []
    for job in jobs:
        # Hledáme v názvu, popisu a dalších textech
        nazev = (job.get('nazev_pozice', '') or '').lower()
        popis = (job.get('popis', '') or '').lower()
        combined_text = f"{nazev} {popis}"

        # Kontrola zda text obsahuje nějaký vyloučený jazykový požadavek
        has_excluded_language = any(
            lang_req.lower() in combined_text
            for lang_req in config.EXCLUDE_LANGUAGE_REQUIREMENTS
        )

        if not has_excluded_language:
            filtered_jobs.append(job)

    return filtered_jobs


def get_scraper_by_name(portal_name: str):
    """
    Vrátí instanci scraperu podle názvu portálu

    Args:
        portal_name: Název portálu (jobs_cz, prace_cz, atd.)

    Returns:
        Instance scraperu nebo None
    """
    scrapers_map = {
        'jobs_cz': JobsCzScraper,
        'prace_cz': PraceCzScraper,
        'startupjobs': StartupJobsScraper,
        'linkedin': LinkedInScraper,
        'indeed': IndeedScraper,
        'profesia': ProfesiaScraper,
    }

    scraper_class = scrapers_map.get(portal_name)
    if scraper_class:
        return scraper_class()
    return None


def run_scraping(portal_filter=None):
    """
    Hlavní funkce pro spuštění scrapování

    Args:
        portal_filter: Volitelně - název konkrétního portálu pro scraping
    """
    logger = logging.getLogger("main")
    logger.info("=" * 80)
    logger.info("Spouštím job scraper")
    logger.info(f"Datum a čas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # Inicializace komponent
    excel_handler = ExcelHandler()
    excel_handler.load_or_create()

    deduplicator = Deduplicator()
    existing_ids = excel_handler.get_existing_ids()
    deduplicator.load_existing_ids(existing_ids)

    relevance_scorer = RelevanceScorer()

    # Získání klíčových slov
    keywords = config.ALL_KEYWORDS
    logger.info(f"Použitých klíčových slov: {len(keywords)}")

    # Určení portálů pro scraping
    if portal_filter:
        # Scraping pouze jednoho portálu
        portals_to_scrape = [portal_filter] if portal_filter in config.TARGET_PORTALS else []
        if not portals_to_scrape:
            logger.error(f"Neznámý portál: {portal_filter}")
            return
    else:
        # Scraping všech povolených portálů
        portals_to_scrape = [
            name for name, settings in config.TARGET_PORTALS.items()
            if settings.get('enabled', True)
        ]

    logger.info(f"Portály pro scraping: {', '.join(portals_to_scrape)}")

    # Statistiky
    total_found = 0
    total_added = 0
    total_duplicates = 0

    # Iterace přes portály
    for portal_name in portals_to_scrape:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Scraping portálu: {portal_name}")
        logger.info(f"{'=' * 80}")

        try:
            # Vytvoření instance scraperu
            scraper = get_scraper_by_name(portal_name)
            if not scraper:
                logger.error(f"Nepodařilo se vytvořit scraper pro {portal_name}")
                continue

            # Scraping
            jobs = scraper.scrape(keywords)
            total_found += len(jobs)
            logger.info(f"Nalezeno {len(jobs)} nabídek na {portal_name}")

            # Filtrování podle lokality
            jobs_before_location_filter = len(jobs)
            jobs = filter_by_location(jobs)
            filtered_by_location = jobs_before_location_filter - len(jobs)
            if filtered_by_location > 0:
                logger.info(f"Vyfiltrováno {filtered_by_location} nabídek podle lokality")

            # Filtrování vyloučených klíčových slov (junior atd.)
            jobs_before_exclude_filter = len(jobs)
            jobs = filter_by_exclude_keywords(jobs)
            filtered_by_keywords = jobs_before_exclude_filter - len(jobs)
            if filtered_by_keywords > 0:
                logger.info(f"Vyfiltrováno {filtered_by_keywords} junior/nežádoucích pozic")

            # Filtrování jazykových požadavků (C1 angličtina, němčina)
            jobs_before_lang_filter = len(jobs)
            jobs = filter_by_language_requirements(jobs)
            filtered_by_languages = jobs_before_lang_filter - len(jobs)
            if filtered_by_languages > 0:
                logger.info(f"Vyfiltrováno {filtered_by_languages} nabídek s nežádoucími jazykovými požadavky")

            logger.info(f"Po filtrování zůstává {len(jobs)} nabídek")

            # Přidání relevance skóre
            jobs = relevance_scorer.add_relevance_to_jobs(jobs)

            # Deduplikace a přidání do Excel
            added_count = 0
            duplicate_count = 0

            for job in jobs:
                # Generování ID a kontrola duplicity
                job_id, is_duplicate = deduplicator.check_and_add(
                    job['nazev_pozice'],
                    job['spolecnost'],
                    job['lokace']
                )

                if is_duplicate:
                    duplicate_count += 1
                    continue

                # Přidání ID do job data
                job['id'] = job_id

                # Přidání do Excel
                if excel_handler.add_job(job):
                    added_count += 1

            total_added += added_count
            total_duplicates += duplicate_count

            logger.info(f"Přidáno: {added_count}, Duplicit: {duplicate_count}")

        except Exception as e:
            logger.error(f"Chyba při scrapování {portal_name}: {e}", exc_info=True)
            # Pokračujeme i při selhání jednoho portálu
            continue

    # Uložení Excel souboru
    excel_handler.save()
    excel_handler.close()

    # Výsledný report
    logger.info("\n" + "=" * 80)
    logger.info("SOUHRN")
    logger.info("=" * 80)
    logger.info(f"Celkem nalezeno nabídek: {total_found}")
    logger.info(f"Nových nabídek přidáno: {total_added}")
    logger.info(f"Duplicit přeskočeno: {total_duplicates}")
    logger.info(f"Excel soubor: {config.EXCEL_OUTPUT_FILE}")
    logger.info("=" * 80)
    logger.info("Scraping dokončen")


def scheduled_run():
    """Funkce pro naplánovaný běh"""
    logger = logging.getLogger("scheduler")
    logger.info("Spouštím naplánovaný běh scraperu")
    run_scraping()


def run_scheduler():
    """Spustí scheduler pro denní běh"""
    logger = logging.getLogger("scheduler")
    logger.info(f"Scheduler spuštěn - denní běh v {config.SCHEDULE_TIME}")

    # Naplánování denního běhu
    schedule.every().day.at(config.SCHEDULE_TIME).do(scheduled_run)

    # Hlavní loop scheduleru
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Kontrola každou minutu
    except KeyboardInterrupt:
        logger.info("Scheduler ukončen uživatelem")


def main():
    """Hlavní entry point"""
    setup_logging()

    parser = argparse.ArgumentParser(
        description='Job Scraper - scraping pracovních nabídek z českých portálů',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Příklady použití:
  python main.py                    # Jednorázové spuštění (všechny portály)
  python main.py --portal jobs_cz   # Scraping pouze jobs.cz
  python main.py --schedule         # Spuštění jako daemon (denně v 8:00)

Podporované portály:
  jobs_cz, prace_cz, startupjobs, linkedin, indeed, profesia
        """
    )

    parser.add_argument(
        '--portal',
        type=str,
        choices=['jobs_cz', 'prace_cz', 'startupjobs', 'linkedin', 'indeed', 'profesia'],
        help='Scraping pouze konkrétního portálu'
    )

    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Spustit jako daemon s denním plánováním'
    )

    args = parser.parse_args()

    if args.schedule:
        # Režim scheduleru
        run_scheduler()
    else:
        # Jednorázové spuštění
        run_scraping(portal_filter=args.portal)


if __name__ == "__main__":
    main()
