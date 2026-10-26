# Etap: dwa programy połączone przez Modbus TCP

## Cel i pliki

Serwer reprezentuje proces oraz zdalny moduł wejść/wyjść. Klient reprezentuje sterownik.
Wymiana danych odbywa się przez TCP, mimo że oba programy działają na jednym komputerze.

- process.py: model zbiornika, bez komunikacji.
- controller.py: regulator z histerezą 40–60%.
- process_server.py: model + serwer Modbus TCP + zapis CSV.
- controller_client.py: odczyt pomiaru, regulator, zapis polecenia.
- requirements.txt: ustalona wersja biblioteki.

To samodzielna kopia ćwiczenia. Nie uruchamiaj równocześnie starego tank.py.
Nie potrzebujesz Dockera w tym etapie.

## Uruchomienie w Windows / PowerShell

Otwórz terminal w folderze zawierającym te pliki.

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Nie trzeba aktywować środowiska ani zmieniać polityki wykonywania PowerShella.
Jeśli zwykle korzystasz z launchera py, zastąp pierwsze python poleceniem py.

Terminal 1:

    .\.venv\Scripts\python.exe process_server.py

Terminal 2, ten sam folder:

    .\.venv\Scripts\python.exe controller_client.py

Uruchom klienta w ciągu kilku sekund po serwerze. Bez klienta pompa jest wyłączona,
a poziom spada; dłuższe oczekiwanie może więc dać inny początkowy pomiar.
Programy pracują do Ctrl+C. Zatrzymuj najpierw klienta, następnie serwer.
Serwer zapisuje modbus_measurements.csv obok swojego pliku; kolejne uruchomienie nadpisuje CSV.

## Mapa danych

Połączenie: 127.0.0.1:1502, klient wysyła Unit ID = 1.
Serwer tej biblioteki udostępnia jeden bank danych, bez oddzielnej mapy dla każdego Unit ID.
Standardowy port Modbus TCP to 502; w ćwiczeniu wybraliśmy 1502.

| Sygnał | Przestrzeń | Adres w protokole i kodzie | Kod funkcji |
|---|---|---|---|
| Poziom | Input Register, 16 bitów | 0 | 04 — Read Input Registers |
| Polecenie pompy | Coil, 1 bit | 0 | 05 — Write Single Coil |

Te dwa adresy 0 należą do różnych przestrzeni danych.
W tradycyjnej notacji dokumentacji mogą występować jako 30001 i 00001.
Do metod biblioteki przekazujemy 0, nie 30001 ani 00001.

Poziom kodujemy jako round(level_pct * 100), np. 5037 oznacza 50,37%.
To liczba całkowita ze skalą, nie float zapisany w rejestrze.
Klient dzieli odczyt przez 100. Kodowanie mieści zakres 0–100% w jednym rejestrze.

Input Register jest tylko do odczytu z perspektywy klienta Modbus.
Lokalny program serwera aktualizuje go metodą bank.set_input_registers().
Ta lokalna aktualizacja nie generuje pakietu TCP.

## Przebieg cyklu

1. Serwer publikuje początkowy poziom 50% i wyłącza pompę.
2. Klient wysyła żądanie FC04 i otrzymuje aktualny zakodowany pomiar.
3. Klient wykonuje regulator i wysyła FC05 z poleceniem pompy.
4. Serwer potwierdza zapis w banku danych.
5. Pętla procesu pobiera polecenie i oblicza kolejny stan zbiornika.

Potwierdzenie FC05 oznacza przyjęcie zapisu, a nie niezależny dowód fizycznej pracy pompy.

Serwer aktualizuje model mniej więcej co 100 ms. W bilansie używa faktycznie
zmierzonego czasu, zamiast zakładać idealne 100 ms. Komenda jest traktowana
jako stała w każdym przedziale modelu; zmiana odebrana w jego trakcie zostanie
uwzględniona w następnym przedziale. To przybliżenie symulacji.

Klient odpytuje mniej więcej co 100 ms; czas cyklu obejmuje też obsługę żądań.
Różne chwile aktualizacji i opóźnienia powodują niewielkie przekroczenia progów.
Dłuższe zatrzymanie systemu nadal zmniejsza dokładność — to nie system hard real-time.

## Obserwacja w Wiresharku

1. Wybierz interfejs „Adapter for loopback traffic capture” (Npcap).
   Ruch 127.0.0.1 nie przechodzi przez kartę Wi-Fi ani Ethernet.
2. Rozpocznij przechwytywanie przed uruchomieniem klienta.
3. Ustaw filtr wyświetlania:

       tcp.port == 1502

4. Jeśli widzisz tylko TCP: zaznacz pakiet zawierający dane, wybierz
   Analyze -> Decode As..., ustaw port TCP 1502 jako Modbus/TCP
   (nazwa może być pokazana jako MBTCP), zatwierdź.
5. Szukaj żądań i odpowiedzi FC04 i FC05. Rozwiń nagłówek Modbus/TCP
   oraz część Modbus, sprawdź adres 0 i wartość.
6. W FC05 włączenie jest kodowane jako 0xFF00, a wyłączenie jako 0x0000.
7. Porównaj Transaction Identifier żądania i odpowiedzi.
8. Zapisz przechwycenie jako PCAPNG do dokumentacji projektu.

Nie oczekuj, że każdy pakiet TCP odpowiada dokładnie jednemu komunikatowi Modbus.
TCP jest strumieniem; Wireshark może składać komunikat z segmentów.

## Kryteria powodzenia

- Klient drukuje kolejne przełączenia pompy w pobliżu 40% oraz 60%.
- Proces reaguje na te polecenia, a przelew pozostaje równy zero.
- W Wiresharku są pary żądanie/odpowiedź FC04 i FC05.
- CSV zawiera zmiany poziomu i stanu pompy.

## Utrata połączenia — zachowanie tej wersji

Brak klienta na starcie: pompa pozostaje wyłączona.
Po utracie klienta serwer zachowuje ostatnie zapisane polecenie; nie ma jeszcze watchdoga.
Zwykłe Ctrl+C klienta próbuje wysłać wyłączenie pompy, ale nie gwarantuje dostarczenia.
Wymuszone zakończenie procesu może ominąć tę próbę.
To świadomy punkt wyjścia do późniejszego ćwiczenia z utratą komunikacji.
Serwer nasłuchuje wyłącznie na 127.0.0.1.

## Diagnostyka

- ModuleNotFoundError: uruchom instalację i oba programy tym samym Pythonem z .venv.
- Brak połączenia: sprawdź uruchomienie serwera oraz zgodność HOST i PORT.
- Zajęty port: zamknij poprzedni serwer.
- Brak pakietów: wybierz interfejs loopback i filtr portu 1502.
- Tylko TCP bez Modbus: zastosuj Decode As.
- Brak interfejsu loopback: sprawdź instalację Npcap w Wiresharku.
- CSV nie daje się nadpisać: zamknij go w programie, który blokuje plik.

## Dokumentacja źródłowa

- Serwer i bank danych:
  https://pymodbustcp.readthedocs.io/en/v0.3.0/package/class_ModbusServer.html
- Klient i funkcje:
  https://pymodbustcp.readthedocs.io/en/v0.3.0/package/class_ModbusClient.html
- Przechwytywanie loopback:
  https://wiki.wireshark.org/CaptureSetup/Loopback

## Sprawdzenie przygotowanych plików

Sprawdzono lokalnie na Pythonie 3.13 i pyModbusTCP 0.3.0:
odczyt pomiaru, odrzucenie adresu poza mapą, zapis i odczyt coil,
przejście regulatora wyłączona -> włączona -> wyłączona,
zapis CSV i brak przelewu w krótkim przebiegu.
Nie wykonywano przechwycenia w Twoim Wiresharku ani integracji z OpenPLC.

