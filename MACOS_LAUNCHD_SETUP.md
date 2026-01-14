# Nastavení automatického spouštění scraperu na macOS

Tento průvodce vás provede nastavením automatického denního spouštění job scraperu pomocí macOS launchd.

## Předpoklady

- macOS systém
- Projekt nainstalovaný v adresáři (např. `~/Documents/scrape_pracovni_nabidky`)
- Python virtual environment vytvořen a funkční
- Scraper již testován a funkční při manuálním spuštění

## Krok 1: Upravit cestu v run_scraper.sh

Otevřete soubor `run_scraper.sh` a upravte cestu `PROJECT_DIR` podle vaší instalace:

```bash
# Změňte tuto cestu na vaši skutečnou cestu
PROJECT_DIR="$HOME/Documents/scrape_pracovni_nabidky"
```

Pokud máte projekt v jiné složce, upravte cestu odpovídajícím způsobem.

## Krok 2: Nastavit práva ke spuštění

Udělejte skript spustitelným:

```bash
cd ~/Documents/scrape_pracovni_nabidky
chmod +x run_scraper.sh
```

## Krok 3: Otestovat skript manuálně

Před nastavením launchd vyzkoušejte, že skript funguje:

```bash
./run_scraper.sh
```

Měli byste vidět výstup scraperu a po dokončení by měl být aktualizován Excel soubor.

## Krok 4: Upravit cz.jobs.scraper.plist

Otevřete soubor `cz.jobs.scraper.plist` a nahraďte **VŠECHNY výskyty** `VASE_UZIVATELSKE_JMENO` vaším skutečným uživatelským jménem na macOS.

Můžete zjistit vaše uživatelské jméno pomocí:

```bash
whoami
```

Nebo použijte tento příkaz pro automatickou úpravu:

```bash
# Zjistěte vaše uživatelské jméno
UZIVATEL=$(whoami)

# Vytvořte upravený plist soubor
sed "s/VASE_UZIVATELSKE_JMENO/$UZIVATEL/g" cz.jobs.scraper.plist > ~/Library/LaunchAgents/cz.jobs.scraper.plist
```

**DŮLEŽITÉ:** Ověřte, že všechny cesty v plist souboru odpovídají skutečnému umístění vašeho projektu!

## Krok 5: Nahrát launchd konfiguraci

Pokud jste nepoužili příkaz `sed` výše, ručně zkopírujte plist soubor:

```bash
cp cz.jobs.scraper.plist ~/Library/LaunchAgents/
```

Načtěte konfiguraci do launchd:

```bash
launchctl load ~/Library/LaunchAgents/cz.jobs.scraper.plist
```

## Krok 6: Ověřit, že je služba načtená

Zkontrolujte, že je služba aktivní:

```bash
launchctl list | grep cz.jobs.scraper
```

Měli byste vidět řádek s názvem služby.

## Krok 7: Otestovat spuštění (volitelné)

Můžete otestovat okamžité spuštění bez čekání na plánovaný čas:

```bash
launchctl start cz.jobs.scraper
```

## Kontrola logů

Logy se ukládají do projektové složky:

```bash
# Výstup scraperu
tail -f ~/Documents/scrape_pracovni_nabidky/launchd.log

# Chyby (pokud nastanou)
tail -f ~/Documents/scrape_pracovni_nabidky/launchd_error.log
```

## Změna času spuštění

Pokud chcete změnit čas denního spuštění, upravte v `cz.jobs.scraper.plist`:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>      <!-- Hodina (0-23) -->
    <key>Minute</key>
    <integer>0</integer>      <!-- Minuta (0-59) -->
</dict>
```

Po úpravě je potřeba službu znovu načíst:

```bash
launchctl unload ~/Library/LaunchAgents/cz.jobs.scraper.plist
launchctl load ~/Library/LaunchAgents/cz.jobs.scraper.plist
```

## Spuštění při více časech

Pokud chcete scraper spustit vícekrát denně (např. 9:00 a 17:00), použijte pole:

```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>17</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

## Zastavení a odstranění služby

Pokud chcete službu zastavit:

```bash
launchctl unload ~/Library/LaunchAgents/cz.jobs.scraper.plist
```

Pokud chcete službu úplně odstranit:

```bash
launchctl unload ~/Library/LaunchAgents/cz.jobs.scraper.plist
rm ~/Library/LaunchAgents/cz.jobs.scraper.plist
```

## Řešení problémů

### Služba se nespouští

1. Zkontrolujte logy v `launchd_error.log`
2. Ověřte, že cesty v plist souboru jsou správné
3. Ověřte, že `run_scraper.sh` je spustitelný (`chmod +x`)
4. Zkuste spustit skript ručně a sledujte chyby

### Permission denied

```bash
chmod +x ~/Documents/scrape_pracovni_nabidky/run_scraper.sh
```

### Python modul nenalezen

Ujistěte se, že:
- Virtual environment je správně aktivovaný v `run_scraper.sh`
- Všechny závislosti jsou nainstalovány v virtual environmentu

### Změny se neprojevují

Po jakýchkoli úpravách plist souboru nebo skriptu:

```bash
launchctl unload ~/Library/LaunchAgents/cz.jobs.scraper.plist
launchctl load ~/Library/LaunchAgents/cz.jobs.scraper.plist
```

## Poznámky

- **Čas spuštění**: Launchd používá 24hodinový formát
- **Cesty**: Používejte absolutní cesty, ne relativní
- **Virtual environment**: Skript automaticky aktivuje venv před spuštěním
- **Deduplicace**: Scraper automaticky kontroluje duplicity, takže opakované spouštění je bezpečné
- **Logování**: Všechny běhy jsou logovány s časovými razítky

## Výhody launchd oproti cron

- ✅ Nativní macOS řešení
- ✅ Automaticky se spustí po restartu systému
- ✅ Lepší správa logů
- ✅ Možnost spuštění při přihlášení (RunAtLoad)
- ✅ Detailní konfigurace prostředí

## Ověření funkčnosti

Po nastavení vyčkejte na naplánovaný čas (9:00) a zkontrolujte:

1. **Log soubor**:
   ```bash
   cat ~/Documents/scrape_pracovni_nabidky/launchd.log
   ```
   Měli byste vidět výstup s časovým razítkem dnešního data v 9:00

2. **Excel soubor**:
   - Otevřete `nabidky_prace.xlsx`
   - Zkontrolujte sloupec "Datum nalezení"
   - Měly by tam být dnešní nabídky

3. **Systémový log**:
   ```bash
   log show --predicate 'subsystem == "com.apple.launchd"' --info --last 1h | grep cz.jobs.scraper
   ```

---

**Hotovo!** 🎉 Váš job scraper se nyní bude automaticky spouštět každý den v 9:00 a kontrolovat nové nabídky.
