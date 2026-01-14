#!/bin/bash
#
# Spouštěcí skript pro job scraper
# Tento skript aktivuje virtuální prostředí a spustí scraper
#

# Nastavení cesty k projektu - UPRAVTE PODLE VAŠÍ INSTALACE
PROJECT_DIR="$HOME/Documents/scrape_pracovni_nabidky"

# Přejdi do adresáře projektu
cd "$PROJECT_DIR" || exit 1

# Aktivuj virtuální prostředí
source "$PROJECT_DIR/venv/bin/activate"

# Spusť scraper s logováním
echo "=================================="
echo "Job Scraper - $(date)"
echo "=================================="

# Spusť scraper
python "$PROJECT_DIR/main.py" --portal jobs_cz

# Výsledek
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "Scraper dokončen úspěšně"
else
    echo "Scraper selhal s kódem $EXIT_CODE"
fi

exit $EXIT_CODE
