# Job Scraper - Automatický monitoring pracovních nabídek

Robustní Python skript pro denní monitoring pracovních nabídek na českých job portálech s automatickou deduplikací a exportem do Excelu.

## 📋 Obsah

- [Funkce](#-funkce)
- [Cílové portály](#-cílové-portály)
- [Instalace](#-instalace)
- [Použití](#-použití)
- [Konfigurace](#-konfigurace)
- [Struktura projektu](#-struktura-projektu)
- [Automatizace](#-automatizace)
- [Omezení a poznámky](#-omezení-a-poznámky)
- [Troubleshooting](#-troubleshooting)

## 🎯 Funkce

- ✅ Automatické scrapování 6 českých pracovních portálů
- ✅ Vyhledávání podle konfigurovatelných klíčových slov
- ✅ Inteligentní deduplikace pomocí MD5 hashů
- ✅ Hodnocení relevance nabídek (High/Medium)
- ✅ Export do strukturovaného Excel souboru
- ✅ Rate limiting a respektování robots.txt
- ✅ Retry logika s exponenciálním backoffem
- ✅ Rotace User-Agent headerů
- ✅ Komplexní error handling a logging
- ✅ Podpora pro scheduled běh (cron/task scheduler)

## 🌐 Cílové portály

| Portál | Status | Poznámka |
|--------|--------|----------|
| jobs.cz | ✅ Implementováno | Největší český job portál |
| prace.cz | ✅ Implementováno | - |
| startupjobs.cz | ✅ Implementováno | Zaměřeno na startupy |
| indeed.cz | ✅ Implementováno | Mezinárodní platforma |
| profesia.cz | ✅ Implementováno | - |
| linkedin.com/jobs | ⚠️ Implementováno | Může vyžadovat autentizaci |

**DŮLEŽITÉ:** HTML selektory v scraperech jsou UKÁZKOVÉ a musí být upraveny podle skutečné struktury jednotlivých webů. Struktura webů se může časem měnit.

## 📦 Instalace

### Požadavky

- Python 3.8 nebo novější
- pip (Python package manager)

### Postup instalace

1. **Klonování nebo stažení repozitáře**

```bash
git clone <repository-url>
cd scrape_pracovni_nabidky
```

2. **Vytvoření virtuálního prostředí (doporučeno)**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalace závislostí**

```bash
pip install -r requirements.txt
```

4. **Nastavení environment variables (volitelné)**

Pro LinkedIn scraping:
```bash
# Linux/Mac
export LINKEDIN_EMAIL="your-email@example.com"
export LINKEDIN_PASSWORD="your-password"

# Windows (CMD)
set LINKEDIN_EMAIL=your-email@example.com
set LINKEDIN_PASSWORD=your-password

# Windows (PowerShell)
$env:LINKEDIN_EMAIL="your-email@example.com"
$env:LINKEDIN_PASSWORD="your-password"
```

## 🚀 Použití

### Základní spuštění

```bash
# Jednorázové spuštění - všechny portály
python main.py

# Scraping pouze konkrétního portálu
python main.py --portal jobs_cz
python main.py --portal linkedin

# Spuštění jako daemon s denním plánováním (8:00)
python main.py --schedule
```

### Podporované portály

```
jobs_cz, prace_cz, startupjobs, linkedin, indeed, profesia
```

### Výstup

Po spuštění se vytvoří:
- **job_listings.xlsx** - Excel soubor s nalezenými nabídkami
- **scraper.log** - Log soubor se záznamy o průběhu

## ⚙️ Konfigurace

Veškerá konfigurace se nachází v souboru `config.py`.

### Klíčová slova

Upravte seznamy klíčových slov podle vašich potřeb:

```python
PRIMARY_KEYWORDS = [
    "projektový manažer",
    "project manager",
    # ... přidejte vlastní
]

SECONDARY_KEYWORDS = [
    "technical project manager",
    "delivery manager",
    # ... přidejte vlastní
]
```

### Profil kandidáta

Upravte profil pro správné hodnocení relevance:

```python
CANDIDATE_PROFILE = {
    "pozice": "Seniorní projektový manažer",
    "zkušenosti_let": 5,
    "oblast": "e-commerce",
    # ... upravte podle potřeby
}
```

### Technické nastavení

```python
# Rate limiting
REQUEST_DELAY_MIN = 2  # minimální delay (sekundy)
REQUEST_DELAY_MAX = 5  # maximální delay (sekundy)

# Scheduling
SCHEDULE_TIME = "08:00"  # čas denního běhu
```

## 📁 Struktura projektu

```
scrape_pracovni_nabidky/
├── main.py                 # Hlavní orchestrátor
├── config.py               # Konfigurace
├── requirements.txt        # Python závislosti
├── README.md              # Dokumentace
├── .gitignore             # Git ignore soubor
├── scrapers/              # Scrapery pro jednotlivé portály
│   ├── __init__.py
│   ├── base_scraper.py    # Abstraktní třída
│   ├── jobs_cz.py
│   ├── prace_cz.py
│   ├── startupjobs.py
│   ├── linkedin.py
│   ├── indeed.py
│   └── profesia.py
├── utils/                 # Utility moduly
│   ├── __init__.py
│   ├── deduplicator.py    # Deduplikace
│   ├── excel_handler.py   # Práce s Excel
│   └── relevance.py       # Scoring relevance
├── job_listings.xlsx      # Výstupní Excel (generován)
└── scraper.log           # Log soubor (generován)
```

## 🤖 Automatizace

### Linux - Cron

Ukázkový crontab záznam je v souboru `cron_example.txt`.

```bash
# Editace crontabu
crontab -e

# Přidání denního běhu v 8:00
0 8 * * * cd /cesta/k/projektu && /cesta/k/venv/bin/python main.py >> /cesta/k/projektu/cron.log 2>&1
```

### Windows - Task Scheduler

Ukázkový skript je v souboru `windows_task_example.bat`.

1. Otevřete Task Scheduler
2. Create Basic Task
3. Trigger: Daily, 8:00 AM
4. Action: Start a program
5. Program: `C:\cesta\k\venv\Scripts\python.exe`
6. Arguments: `main.py`
7. Start in: `C:\cesta\k\projektu`

## ⚠️ Omezení a poznámky

### LinkedIn

- **Může vyžadovat autentizaci** - implementace bez autentizace může být blokována
- **Doporučení:** Použít LinkedIn API nebo Selenium s přihlášením
- Nastavte environment variables `LINKEDIN_EMAIL` a `LINKEDIN_PASSWORD`

### Scraping omezení

- **Některé portály mohou blokovat scraping** - používejte zodpovědně
- **HTML struktura se mění** - selektory je potřeba pravidelně aktualizovat
- **Rate limiting** - respektujte omezení portálů, používejte přiměřené delays

### robots.txt

Vždy respektujte robots.txt jednotlivých portálů. Příklad kontroly:

```bash
curl https://www.jobs.cz/robots.txt
```

### Právní poznámka

- Scraping může být v rozporu s Terms of Service některých portálů
- Používejte pouze pro osobní účely
- Neukládejte a nešiřte citlivá data

## 🔧 Troubleshooting

### Problém: ModuleNotFoundError

**Řešení:**
```bash
# Ujistěte se, že máte nainstalované všechny závislosti
pip install -r requirements.txt

# Ujistěte se, že jste v aktivovaném virtuálním prostředí
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Problém: Nenalezeny žádné nabídky

**Možné příčiny:**
1. HTML struktura webu se změnila - aktualizujte selektory v příslušném scraperu
2. Web blokuje scraping - zkontrolujte robots.txt a User-Agent
3. Problém s připojením - zkontrolujte log soubor

**Řešení:**
```bash
# Zkontrolujte log
cat scraper.log

# Zkuste konkrétní portál s debug logováním
# Upravte config.py: LOG_LEVEL = "DEBUG"
python main.py --portal jobs_cz
```

### Problém: LinkedIn vyžaduje login

**Řešení:**
1. Nastavte environment variables s credentials
2. Nebo upravte `config.py` a nastavte `"enabled": False` pro LinkedIn

### Problém: Excel soubor se nepodaří otevřít

**Možná příčina:** Soubor je otevřený v jiné aplikaci

**Řešení:**
1. Zavřete Excel soubor před spuštěním scraperu
2. Nebo změňte název výstupního souboru v `config.py`

## 📊 Struktura Excel výstupu

| Sloupec | Popis | Příklad |
|---------|-------|---------|
| ID | Unikátní MD5 hash | `a3f5b8c2d1e9...` |
| Datum nalezení | YYYY-MM-DD | `2024-01-15` |
| Název pozice | Originální název | `Senior Project Manager` |
| Společnost | Zaměstnavatel | `ABC Company s.r.o.` |
| Lokace | Místo výkonu | `Praha - Hybrid` |
| Typ úvazku | Plný/částečný/remote | `Plný úvazek` |
| Portál | Zdroj | `jobs.cz` |
| URL | Odkaz na inzerát | `https://...` |
| Mzda | Pokud uvedena | `80 000 - 100 000 Kč` |
| Relevance | High/Medium | `High` |
| Status | New/Seen/Applied | `New` |
| Poznámky | Vlastní poznámky | - |

## 🤝 Přispívání

Příspěvky jsou vítány! Hlavní oblasti pro zlepšení:

1. **Aktualizace HTML selektorů** pro jednotlivé portály
2. **LinkedIn autentizace** pomocí Selenium
3. **Nové portály** - přidání dalších job portálů
4. **Tests** - jednotkové testy pro scrapery
5. **GUI** - grafické rozhraní pro konfiguraci

## 📝 Licence

Tento projekt je určen pouze pro osobní a vzdělávací účely.

## 👤 Autor

Vytvořeno pro monitoring pracovních nabídek pro seniorní projektové manažery v oblasti e-commerce.

---

**Poslední aktualizace:** 2024-01-15
