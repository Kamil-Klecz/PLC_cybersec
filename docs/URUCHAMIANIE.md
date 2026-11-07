# Odtworzenie i uruchomienie PLCSim

Instrukcja dla **Windows 11, Intel/AMD 64-bit**. Docker Desktop jest już
zainstalowany. Potrzebne jest połączenie z Internetem.

Wykonuj kroki po kolei. Polecenia wpisuj w **PowerShellu**, bez kopiowania
znaczników otaczających bloki kodu.

`C:\OT\PLCSim` w poleceniach jest przykładową lokalizacją na nowym komputerze.
Na obecnym komputerze projekt znajduje się w `D:\Coding\repos\PLC_cybersec`;
jeśli używasz innej lokalizacji, podstaw ją we wszystkich poleceniach `cd`.

## 1. Pobierz projekt

1. Otwórz repozytorium projektu na GitHubie.
2. Kliknij **Code → Download ZIP**.
3. Rozpakuj archiwum. Przenieś i nazwij folder tak, aby plik `process_server.py`
   znajdował się pod `C:\OT\PLCSim\process_server.py`.
4. W tym samym folderze muszą znajdować się `requirements.txt`, `TankControl`
   oraz `hmi`. Sprawdź też obecność pliku
   `hmi/scada-lts-config-ZAIMPORTUJ-DO-SCADALTS.json`. Nie pracuj bezpośrednio
   wewnątrz ZIP-a. Jeśli pliku JSON nie ma w pobranym repozytorium, trzeba go
   najpierw dodać i opublikować z komputera, na którym skonfigurowano HMI.

## 2. Zainstaluj Pythona i OpenPLC Editor

1. Z [Python Releases for Windows](https://www.python.org/downloads/windows/)
   pobierz **Python 3.13.x → Windows installer (64-bit)**. Nie wybieraj
   pakietu embeddable ani ARM64.
2. Uruchom instalator. Zaznacz **Add python.exe to PATH**, pozostaw instalację
   `pip` i launchera `py`, następnie kliknij **Install Now**.
3. Z [wydania OpenPLC Editor 4.3.2](https://github.com/Autonomy-Logic/openplc-editor/releases/tag/v4.3.2)
   w sekcji **Assets** pobierz **`OpenPLC.Editor_4.3.2.exe`** i zainstaluj.
   Nie wybieraj pliku ARM64 ani archiwum Source code.
4. Otwórz nowe okno PowerShella i sprawdź:

   ```powershell
   py -3.13 --version
   ```

   Wynik powinien zaczynać się od `Python 3.13`.

## 3. Przygotuj zależności Pythona

W PowerShellu wykonaj:

```powershell
cd C:\OT\PLCSim
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "import pyModbusTCP; print('Python OK')"
```

**Wynik:** `Python OK`. Nie trzeba aktywować środowiska `.venv`.

## 4. Uruchom Docker Desktop i kontenery HMI

1. Uruchom Docker Desktop i poczekaj na gotowość silnika.
2. Używaj **Linux containers**. Jeżeli menu Docker Desktop zawiera
   **Switch to Linux containers**, kliknij tę pozycję.
3. W tym samym PowerShellu wykonaj:

   ```powershell
   docker info --format '{{.OSType}}'
   ```

   Oczekiwany wynik: `linux`.
4. Uruchom HMI i bazę:

   ```powershell
   docker compose -f hmi/compose.yaml up -d
   docker compose -f hmi/compose.yaml ps
   ```

**Wynik:** kontener bazy osiąga stan `healthy`, a kontener `scadalts` jest
uruchomiony. Pierwszy start może potrwać kilka minut. Ten krok tworzy też
sieć `ot-supervision` potrzebną PLC.

## 5. Utwórz kontener PLC

pobierz oficjalny obraz Runtime.
Wykonaj **raz, przy pierwszej instalacji**:

```powershell
docker pull ghcr.io/autonomy-logic/openplc-runtime:latest
docker run -d --name ot-plc --network ot-supervision -p 127.0.0.1:8443:8443 --cap-add=SYS_NICE --cap-add=SYS_RESOURCE -v ot-plc-data:/var/run/runtime ghcr.io/autonomy-logic/openplc-runtime:latest
```

Sprawdź:

```powershell
docker ps --filter name=ot-plc
curl.exe -k https://127.0.0.1:8443/api/version
```

**Wynik:** kontener ma status `Up`, a drugie polecenie zwraca wersję Runtime.
Jeśli API jeszcze nie odpowiada, odczekaj kilkanaście sekund i ponów sprawdzenie.
Portu 8443 nie otwieraj jako panelu w przeglądarce — służy OpenPLC Editorowi.

## 6. Uruchom symulator procesu

Otwórz **drugie okno PowerShella** i wykonaj:

```powershell
cd C:\OT\PLCSim
.\.venv\Scripts\python.exe process_server.py
```

**Pozostaw to okno otwarte.** Powinien pojawić się komunikat
`Serwer: 0.0.0.0:1502` i kolejne pomiary. Przed uruchomieniem programu PLC
poziom może spaść do zera. W logu `polecenie` to ostatni coil zapisany przez
PLC, `pompa` to stan zastosowany w modelu, a `komunikacja=0` oznacza brak
jeszcze pierwszego zapisu polecenia albo brak nowego zapisu przez ponad
2 sekundy. Wtedy model wymusza `pompa=0`.
Każde uruchomienie skryptu nadpisuje `modbus_measurements.csv`; zachowaj
poprzedni przebieg przed restartem, jeśli chcesz go porównać.

Jeśli Windows zapyta o dostęp Pythona do sieci, zezwól na dostęp w używanej
prywatnej sieci. Nie wyłączaj całej zapory Windows.

W pierwszym PowerShellu sprawdź połączenie z kontenera:

```powershell
docker exec ot-plc python3 -c "import socket; s=socket.create_connection(('host.docker.internal',1502),timeout=3); print('TCP OK'); s.close()"
```

**Wynik:** `TCP OK`. W razie błędu sprawdź, czy skrypt nadal działa oraz czy
w `process_server.py` jest `HOST = "0.0.0.0"` i `PORT = 1502`.

## 7. Wgraj program do PLC

1. Uruchom **OpenPLC Editor**.
2. Wybierz **Open Project** i otwórz istniejący projekt z folderu
   `C:\OT\PLCSim\TankControl`. Plikiem projektu jest `project.json`.
   Nie twórz nowego projektu.
3. W konfiguracji **Device** wybierz **OpenPLC Runtime v4**.
4. W polu adresu IP wpisz **`127.0.0.1`** — bez portu i bez `https://`.
5. Kliknij **Connect**. Przy pierwszym połączeniu utwórz użytkownika Runtime
   i zapisz jego dane logowania. To nie jest konto Scada-LTS.
6. Zapisz projekt, wybierz **Build & Upload** i poczekaj na zakończenie
   kompilacji oraz przesyłania. Pozwól Editorowi pobrać wymagane narzędzia,
   jeżeli poprosi o ich instalację.
7. Kliknij **Start / Play**, jeżeli PLC jeszcze nie pracuje.
8. W debuggerze obserwuj `LevelRaw`, `LevelPct` i `PumpCmd`.

**Wynik:** poziom zmienia się w pobliżu 40–60%, a pompa przełącza stan.

Konfiguracja komunikacji jest już w repozytorium. Nie dodawaj jej ponownie:

| Element | Oczekiwane ustawienie |
|---|---|
| `TankIO` | `host.docker.internal`, port `1502`, Unit ID `1` |
| `LevelRead` | FC04, offset `0`, długość `1`, cykl `100 ms` |
| `PumpWrite` | FC05, offset `0`, długość `1`, cykl `100 ms` |
| `TankHmi` | włączony serwer Modbus, `0.0.0.0`, port `502` |

## 8. Zaimportuj konfigurację HMI na nowym komputerze

Konfiguracja utworzona w interfejsie Scada-LTS mieszka w bazie MySQL w wolumenie
Dockera `ot-hmi_scada-db`, a nie w plikach Compose. Eksport JSON w
`hmi/scada-lts-config-ZAIMPORTUJ-DO-SCADALTS.json` zawiera źródło
`OpenPLC_Tank`, punkty `Tank_Level` i `Tank_PumpCmd`, listy obserwacyjne oraz
widok `Tank_HMI`. Nie zawiera historii pomiarów ani kont użytkowników.

Ten krok wykonaj **raz na nowej, pustej instancji Scada-LTS**, po uruchomieniu
kontenerów i PLC. Przy zwykłym ponownym uruchomieniu na tym samym komputerze
nie importuj konfiguracji ponownie: baza pozostaje w wolumenie.

1. Otwórz [Scada-LTS](http://127.0.0.1:8080/Scada-LTS/) i zaloguj się.
   Na świeżej instalacji konto początkowe to `admin` / `admin`; ustaw własne
   hasło po pierwszym logowaniu.
2. Otwórz [Import/Export](http://127.0.0.1:8080/Scada-LTS/emport.shtm).
3. Otwórz lokalny plik `hmi/scada-lts-config-ZAIMPORTUJ-DO-SCADALTS.json` w
   edytorze tekstu. Skopiuj **całą** jego zawartość do pola **Data** na stronie
   Import/Export i kliknij **Import** w sekcji importu JSON. Poczekaj na wynik
   importu i sprawdź komunikaty o błędach.
4. W **Data sources** sprawdź, czy `OpenPLC_Tank` ma host `ot-plc`, port `502`
   i jest włączone. Sprawdź odczyt obu punktów w **Watch List** oraz otwórz
   **Graphical views → Tank_HMI**.

Na tym kończy się konfiguracja HMI na nowym komputerze; **pomiń kroki 9–11**.
Wykorzystane w widoku grafiki `Vertical level` i `Scada-LTS-Pump` pochodzą z
obrazu Scada-LTS. Jeśli później dodasz własne grafiki lub tło przesłane do
aplikacji, sam eksport JSON nie przeniesie tych plików.

Nie używaj tutaj opcji **Import Project** dla pełnego archiwum ZIP. Taki import
zastępuje zawartość docelowej bazy, w tym konta użytkowników; służy do pełnego
odtworzenia instancji, a nie do tego kroku.

## 9. Ręcznie utwórz źródło danych w Scada-LTS (bez eksportu JSON)

Jeśli nie masz pliku eksportu z kroku 8, wykonaj kroki 9–11 ręcznie, jeden raz
na nowej bazie. Jeśli import się powiódł, nie twórz tych obiektów ponownie.

1. Otwórz [Scada-LTS](http://127.0.0.1:8080/Scada-LTS/).
2. Zaloguj się: użytkownik **`admin`**, hasło **`admin`**. Ustaw następnie
   własne hasło w edycji użytkownika.
3. Otwórz **Data sources**. Kliknij dodawanie źródła (**Add / +**), wybierz
   typ **Modbus IP** i wypełnij:

   | Pole | Wartość |
   |---|---|
   | Name | `OpenPLC_Tank` |
   | Transport | `TCP` |
   | Host | `ot-plc` |
   | Port | `502` |
   | Update period | `500`, jednostka `Milliseconds` |
   | Timeout | `1000` ms |
   | Retries | `1` |
   | Max read bit count | `2000` |
   | Max read register count | `125` |
   | Max write register count | `120` |
   | Encapsulated | wyłączone |

4. Kliknij **Save**. Pozostaw automatycznie wygenerowany **XID**.
5. Włącz źródło przełącznikiem jego stanu na liście źródeł.

## 10. Ręcznie utwórz dwa punkty danych

1. Otwórz edycję źródła **`OpenPLC_Tank`**.
2. W sekcji **Points** kliknij dodawanie punktu (**Add point / +**).
3. W formularzu **Point details** ustaw kolumnę `Tank_Level` z tabeli poniżej.
   Kliknij **Save** i włącz zapisany punkt na liście **Points**.
4. Ponownie kliknij dodawanie punktu. Ustaw kolumnę `Tank_PumpCmd`, zapisz
   i również włącz ten punkt.

| Pole | `Tank_Level` | `Tank_PumpCmd` |
|---|---|---|
| Name | `Tank_Level` | `Tank_PumpCmd` |
| XID | automatycznie wygenerowane | automatycznie wygenerowane |
| Slave id | `1` | `1` |
| Register range | `Input register` | `Coil status` |
| Modbus data type | `2 byte unsigned integer` | `Binary`, jeśli jest wybór typu |
| Offset | `0` | `0` |
| Settable | wyłączone | wyłączone |
| Multiplier | `0.01` | nie dotyczy |
| Additive | `0` | nie dotyczy |

Pola nieużywane dla wybranego typu pozostaw domyślne. W edycji właściwości
`Tank_Level` ustaw **Logging type → All data**, aby zapisywać dane do wykresu.

## 11. Wyświetl wartości i wykres po ręcznej konfiguracji

1. Otwórz **Watch List**.
2. Przyciskiem **+** utwórz listę obserwacyjną i wybierz ją jako aktywną.
3. Otwórz selektor dostępnych punktów. W nowym interfejsie służy do tego
   ikona bazy danych po prawej stronie nagłówka **Point value dashboard**.
4. Rozwiń źródło `OpenPLC_Tank` i dodaj `Tank_Level` oraz `Tank_PumpCmd`
   do aktywnej listy.
5. Przy wierszu `Tank_Level` kliknij ikonę wykresu słupkowego.
6. W części **DataPoint chart** wybierz **LIVE**, zakres **1 Minute(s)**
   oraz **Real-time update**. Poczekaj na zebranie kilku odczytów.

**Projekt działa, gdy:** poziom na liście zmienia się w pobliżu 40–60,
polecenie pompy przełącza się między 0/1 lub false/true, a wykres pokazuje
naprzemienne napełnianie i opróżnianie. Wartość poziomu ma postać np. `50.37`,
nie `5037`.

## Zapisz późniejsze zmiany HMI w repozytorium

Gdy zmienisz punkty, Watch List albo widok graficzny w Scada-LTS, zaktualizuj
eksport. Samo kliknięcie **Save** w HMI aktualizuje bazę, ale nie plik w repo.

1. Otwórz [Import/Export](http://127.0.0.1:8080/Scada-LTS/emport.shtm).
2. W sekcji **Export** zaznacz **Data sources**, **Data points**,
   **Watch Lists** i **Graphical views**. Nie zaznaczaj **Point values** ani
   **Users**, jeśli chcesz przenieść tylko konfigurację laboratorium.
3. Kliknij **Generate JSON**. Skopiuj zawartość pola **Data** i zastąp nią
   zawartość pliku `hmi/scada-lts-config-ZAIMPORTUJ-DO-SCADALTS.json`.
4. Sprawdź plik przed dodaniem do Git, szczególnie pod kątem haseł i danych,
   których nie chcesz publikować. Sprawdź też, czy plik jest śledzony przez Git:

   ```powershell
   git status --short hmi/scada-lts-config-ZAIMPORTUJ-DO-SCADALTS.json
   ```

   `??` oznacza nowy, jeszcze nieśledzony plik. Dopóki nie dodasz go do Git i
   nie opublikujesz zmian, pobranie repozytorium na drugim komputerze go nie
   zawiera.

## Kolejne uruchomienia

Nie powtarzaj instalacji, tworzenia kontenera, użytkowników ani punktów HMI.

1. Uruchom Docker Desktop.
2. W PowerShellu:

   ```powershell
   cd C:\OT\PLCSim
   docker compose -f hmi/compose.yaml up -d
   docker start ot-plc
   .\.venv\Scripts\python.exe process_server.py
   ```

3. Pozostaw terminal procesu otwarty. W Editorze połącz się z Runtime i sprawdź
   stan PLC. Jeśli jest zatrzymany, kliknij **Start**; jeśli jest pusty,
   ponownie wykonaj **Build & Upload** i **Start**.
4. Otwórz Scada-LTS, listę `Watchlist1` lub widok `Tank_HMI`.
   Nie powtarzaj importu JSON przy każdym starcie.

## Zatrzymanie

1. W Editorze zatrzymaj PLC przyciskiem **Stop**.
2. W terminalu procesu naciśnij **Ctrl+C**.
3. W drugim PowerShellu, w folderze projektu:

   ```powershell
   docker stop ot-plc
   docker compose -f hmi/compose.yaml stop
   ```

Nie usuwaj wolumenów: zawierają konta i konfigurację. Nie wykonuj
`docker compose down -v`, jeśli chcesz zachować HMI.

## Jeśli coś nie działa

| Objaw | Sprawdzenie / poprawka |
|---|---|
| `py` nie jest rozpoznawane | Zainstaluj launcher Pythona i otwórz nowe okno PowerShella. |
| Nie znaleziono `requirements.txt` | Wykonaj `cd C:\OT\PLCSim`; sprawdź, czy nie ma dodatkowego zagnieżdżonego folderu po rozpakowaniu ZIP-a. |
| Docker nie odpowiada | Uruchom Docker Desktop; `docker info --format '{{.OSType}}'` ma zwracać `linux`. |
| Nazwa `ot-plc` jest zajęta | Kontener już istnieje. Zamiast ponawiać `docker run`, wykonaj `docker start ot-plc`. |
| Editor nie łączy się z PLC | W polu IP ma być samo `127.0.0.1`. Sprawdź `curl.exe -k https://127.0.0.1:8443/api/version`. |
| Test `TCP OK` nie przechodzi | Sprawdź uruchomienie serwera Pythona, nasłuch `0.0.0.0:1502` i dostęp aplikacji przez zaporę Windows. |
| Scada-LTS jeszcze się nie otwiera | Wykonaj `docker compose -f hmi/compose.yaml ps` oraz `docker compose -f hmi/compose.yaml logs --tail 80 scadalts`. Baza musi być `healthy`. |
| Watch List jest pusta | Dodaj punkty do listy; samo utworzenie punktów nie dodaje ich do widoku. |
| Są nazwy punktów, lecz brak wartości | Włącz źródło i oba punkty. Sprawdź host `ot-plc`, port `502` oraz niezerowe limity odczytu z kroku 9. |
| `Invalid number of registers: 1` | Ustaw **Max read register count = 125**, zapisz i wyłącz/włącz źródło. |
| Po pobraniu repozytorium brakuje konfiguracji HMI | Sprawdź, czy plik eksportu JSON był śledzony przez Git i znajduje się w folderze `hmi`. Następnie wykonaj krok 8. |
| Brak połączenia HMI–PLC po odtworzeniu kontenera | Wykonaj `docker network connect ot-supervision ot-plc`; komunikat, że połączenie już istnieje, oznacza, że ten krok jest wykonany. |

Źródła instalacji: [OpenPLC Runtime — Docker](https://github.com/Autonomy-Logic/openplc-runtime/blob/main/docs/DOCKER.md),
[Scada-LTS — uruchomienie](https://github.com/SCADA-LTS/Scada-LTS/wiki),
[Scada-LTS — eksport i import konfiguracji](https://github.com/SCADA-LTS/Scada-LTS/wiki/Remote-Export-and-Import-of-project-configuration).
