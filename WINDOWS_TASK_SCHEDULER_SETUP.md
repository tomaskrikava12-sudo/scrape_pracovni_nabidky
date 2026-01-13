# Windows Task Scheduler - Průvodce nastavením

Návod pro automatické spouštění Job Scraperu pomocí Windows Task Scheduler.

## 📋 Požadavky

- Windows 10/11 nebo Windows Server
- Administrátorská práva (pro vytvoření scheduled tasku)
- Nainstalovaný Job Scraper projekt
- Python virtual environment

## 🚀 Postup nastavení

### Krok 1: Příprava BAT skriptu

1. **Otevřete soubor `windows_task_example.bat`**

2. **Upravte cesty podle vaší instalace:**

```batch
SET PROJECT_DIR=C:\Users\VaseJmeno\scrape_pracovni_nabidky
SET PYTHON_EXE=C:\Users\VaseJmeno\scrape_pracovni_nabidky\venv\Scripts\python.exe
```

3. **Volitelně: Nastavte LinkedIn credentials:**

```batch
SET LINKEDIN_EMAIL=vase-email@example.com
SET LINKEDIN_PASSWORD=vase-heslo
```

4. **Uložte soubor**

### Krok 2: Otevření Task Scheduler

**Způsob 1 - Start Menu:**
1. Stiskněte `Win + S`
2. Napište "Task Scheduler"
3. Otevřete aplikaci

**Způsob 2 - Run dialog:**
1. Stiskněte `Win + R`
2. Napište `taskschd.msc`
3. Stiskněte Enter

### Krok 3: Vytvoření nového tasku

1. V pravém panelu klikněte na **"Create Basic Task..."**

2. **Pojmenujte task:**
   - Name: `Job Scraper - Daily Run`
   - Description: `Automatické scrapování pracovních nabídek`
   - Klikněte **Next**

### Krok 4: Nastavení triggeru (časovač)

1. **Vyberte frekvenci:**
   - ☑️ **Daily** (Denně)
   - Klikněte **Next**

2. **Nastavte čas:**
   - Start date: `Dnešní datum`
   - Start time: `08:00:00` (nebo dle preference)
   - Recur every: `1 days`
   - Klikněte **Next**

### Krok 5: Nastavení akce

1. **Vyberte akci:**
   - ☑️ **Start a program**
   - Klikněte **Next**

2. **Nastavte program:**
   - **Program/script:**
     ```
     C:\Users\VaseJmeno\scrape_pracovni_nabidky\windows_task_example.bat
     ```

   - **Start in (optional):**
     ```
     C:\Users\VaseJmeno\scrape_pracovni_nabidky
     ```

   - Klikněte **Next**

### Krok 6: Dokončení

1. **Zkontrolujte nastavení:**
   - Zkontrolujte shrnutí všech nastavení
   - ☑️ **Open the Properties dialog for this task when I click Finish**
   - Klikněte **Finish**

### Krok 7: Pokročilá nastavení (Properties dialog)

V Properties dialogu upravte následující:

#### Záložka "General":
- ☑️ **Run whether user is logged on or not**
- ☑️ **Run with highest privileges** (pokud potřebujete)
- **Configure for:** `Windows 10` (nebo vaše verze)

#### Záložka "Triggers":
- Dvakrát klikněte na trigger pro úpravu
- Můžete přidat další triggery (např. 17:00)
- **Advanced settings:**
  - ☑️ **Enabled**
  - Můžete nastavit: Repeat task every X hours

#### Záložka "Actions":
- Zkontrolujte, že cesta k BAT souboru je správná

#### Záložka "Conditions":
- ☐ **Start the task only if the computer is on AC power** (vypněte pro notebooky)
- ☑️ **Wake the computer to run this task** (volitelné)
- ☑️ **Start only if the following network connection is available: Any** (důležité!)

#### Záložka "Settings":
- ☑️ **Allow task to be run on demand**
- ☑️ **Run task as soon as possible after a scheduled start is missed**
- ☐ **Stop the task if it runs longer than:** (vypněte, nebo nastavte na 1 hour)
- **If the task is already running:** `Do not start a new instance`

### Krok 8: Uložení

1. Klikněte **OK**
2. Pokud jste vybrali "Run whether user is logged on or not", budete požádáni o zadání hesla
3. Zadejte své Windows heslo

## 🧪 Testování

### Test 1: Ruční spuštění

1. V Task Scheduler Library najděte váš task: `Job Scraper - Daily Run`
2. Pravý klik → **Run**
3. Sledujte status v dolní části okna
4. Zkontrolujte log soubor:
   ```
   C:\Users\VaseJmeno\scrape_pracovni_nabidky\windows_task.log
   ```

### Test 2: Kontrola výstupu

1. Otevřete log soubor `windows_task.log`
2. Měli byste vidět:
   ```
   ============================================
   Job Scraper Run - 15.01.2024 08:00:00
   ============================================
   ... scraper output ...
   Scraper dokoncen uspesne
   ```

3. Zkontrolujte Excel soubor: `job_listings.xlsx`

## 🔧 Troubleshooting

### Problém 1: Task se nespustí

**Možné příčiny:**
- Chybná cesta k BAT souboru
- Chybná cesta k Pythonu
- Nedostatečná oprávnění

**Řešení:**
1. Zkontrolujte cesty v BAT souboru
2. Zkuste spustit BAT soubor ručně (dvojklik)
3. Zkontrolujte Task History v Task Scheduler

### Problém 2: Task běží, ale nic se nestane

**Možné příčiny:**
- Chybný working directory
- Chybějící Python závislosti
- Problémy s virtual environment

**Řešení:**
1. Zkontrolujte "Start in" cestu v Properties
2. Otevřete PowerShell a spusťte BAT ručně:
   ```powershell
   cd C:\Users\VaseJmeno\scrape_pracovni_nabidky
   .\windows_task_example.bat
   ```
3. Zkontrolujte `windows_task.log` pro chyby

### Problém 3: "Last Run Result: 0x1"

**Význam:** Obecná chyba

**Řešení:**
1. Zkontrolujte log soubor pro detaily
2. Spusťte BAT soubor ručně v PowerShell
3. Zkontrolujte, že všechny cesty jsou správné

### Problém 4: Task neběží když nejste přihlášeni

**Řešení:**
1. Properties → General tab
2. ☑️ **Run whether user is logged on or not**
3. Zadejte heslo
4. Zkontrolujte, že uživatelský účet má oprávnění

## 📊 Monitorování

### Zobrazení historie tasků:

1. V Task Scheduler vyberte váš task
2. Záložka **History** (pokud není vidět, v menu View → **Enable All Tasks History**)
3. Uvidíte všechny spuštění a jejich výsledky

### Kontrola logů:

```powershell
# Zobrazit poslední řádky logu
Get-Content C:\Users\VaseJmeno\scrape_pracovni_nabidky\windows_task.log -Tail 50

# Sledovat log v reálném čase
Get-Content C:\Users\VaseJmeno\scrape_pracovni_nabidky\windows_task.log -Wait -Tail 10
```

## 🔄 Běžné konfigurace

### Konfigurace 1: Denně v 8:00
- Trigger: Daily, 08:00
- Recur: Every 1 days

### Konfigurace 2: Dvakrát denně (8:00 a 17:00)
- Trigger 1: Daily, 08:00
- Trigger 2: Daily, 17:00
- Pro přidání druhého triggeru: Properties → Triggers → New

### Konfigurace 3: Pouze pracovní dny
- Trigger: Daily, 08:00
- Zaškrtněte dny: Monday, Tuesday, Wednesday, Thursday, Friday

### Konfigurace 4: Každé 3 hodiny
- Trigger: Daily, 00:00
- Advanced settings: ☑️ Repeat task every 3 hours
- For a duration of: Indefinitely

## 📝 Poznámky

1. **Oprávnění:**
   - Task běží s oprávněními uživatele, který ho vytvořil
   - Pro systémové účely použijte SYSTEM účet

2. **Logování:**
   - Doporučujeme pravidelně kontrolovat `windows_task.log`
   - Log může růst - zvažte rotaci logů

3. **Network:**
   - Ujistěte se, že "Network connection available" je zaškrtnuto
   - Scraping vyžaduje internetové připojení

4. **Security:**
   - Hesla v BAT souboru jsou v plain textu
   - Zvažte použití Windows Credential Manager
   - Nebo environment variables z User/System Properties

---

**Další informace:** README.md

**Support:** Zkontrolujte scraper.log a windows_task.log pro detaily
