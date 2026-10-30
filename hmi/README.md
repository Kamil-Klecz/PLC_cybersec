# HMI: Scada-LTS dla TankControl

Codzienne uruchamianie i zatrzymywanie całego laboratorium opisuje
[instrukcja uruchamiania](../docs/URUCHAMIANIE.md). Ten plik dotyczy konfiguracji HMI.

## Architektura

Przegladarka -> Scada-LTS -> serwer Modbus PLC -> obraz I/O PLC.
PLC jako klient Modbus nadal komunikuje sie z process_server.py na Windowsie.
Nie uruchamiaj controller_client.py podczas sterowania przez PLC.

Pierwsza wersja panelu sluzy do obserwacji: poziom, polecenie pompy, trend i alarmy.
PumpCmd jest poleceniem sterownika, nie pomiarem rzeczywistej pracy urzadzenia.

## 1. Udostepnij dane PLC w OpenPLC Editor

W projekcie TankControl:
1. Zatrzymaj PLC.
2. Plus przy projekcie -> Server -> Modbus / TCP; nazwa TankHmi.
3. Enabled: ON, Network Interface: 0.0.0.0, Port: 502.
4. W Buffer Mapping sprawdz:
   - Input Registers: liczba %IW co najmniej 1,
   - Coils: liczba %QX co najmniej 8.
5. W Address Mapping Reference potwierdz:
   - Input Register 0 <-> %IW0 (TankLevelInput / LevelRaw),
   - Coil 0 <-> %QX0.0 (TankPumpOutput / PumpCmd).
6. Zapisz, Build & Upload, uruchom PLC.
Nie zmieniaj TankIO ani kodu regulatora.
Nie dodawaj nowych zmiennych z tymi samymi adresami.

Runtime pelni dwie role:
- klient Modbus do zdalnych I/O, port docelowy 1502;
- serwer Modbus dla HMI, port nasluchiwania 502.
Port 8443 nadal sluzy Editorowi.

## 2. Uruchom Scada-LTS

Uruchom Docker Desktop i kontener ot-plc.
W PowerShellu w D:\Coding\repos\PLCSim:

    docker compose -f hmi/compose.yaml up -d
    docker network connect ot-supervision ot-plc

Polaczenie sieci wykonuje sie raz dla danego kontenera.
Jesli Docker poinformuje, ze kontener juz nalezy do tej sieci, nie trzeba go dodawac ponownie.
Po usunieciu i odtworzeniu ot-plc trzeba powtorzyc podlaczenie do sieci.

Diagnostyka:

    docker compose -f hmi/compose.yaml ps
    docker compose -f hmi/compose.yaml logs --tail 80 scadalts
    docker compose -f hmi/compose.yaml logs --tail 80 database

Baza musi przejsc w healthy, potem Tomcat wdraza aplikacje.
Stan kontenera Up nie oznacza jeszcze gotowosci aplikacji HTTP.

Otworz:
http://127.0.0.1:8080/Scada-LTS/

Domyslne konto czystej instalacji Scada-LTS: admin / admin.
Po pierwszym logowaniu ustaw wlasne haslo i zachowaj je u siebie.

Compose oparto na konfiguracji projektu Scada-LTS.
Uzywa jej domyslnych danych JDBC root/root, bazy scadalts i nazwy hosta database.
Baza nie ma portu opublikowanego na Windowsie, a panel HTTP jest dostepny na loopback.
Dane punktow, widokow i historia znajduja sie w wolumenie scada-db.
Nie uzywaj down -v, jesli chcesz je zachowac.

Obraz Scada-LTS ma poczatkowo tag latest. Po pierwszym udanym uruchomieniu zapisz
digesty obu obrazow i przypnij je w Compose, aby kolejne odtworzenia nie pobieraly
innej wersji:

    docker image inspect scadalts/scadalts:latest --format '{{index .RepoDigests 0}}'
    docker image inspect mysql/mysql-server:8.0.32 --format '{{index .RepoDigests 0}}'

Wynik scadalts/scadalts@sha256:... mozesz wstawic jako image zamiast tagu latest.

## 3. Zrodlo danych w Scada-LTS

Data sources -> nowy typ Modbus IP:
- Name: OpenPLC_Tank
- Transport: TCP
- Host: ot-plc
- Port: 502
- Update period: 500 ms (albo 0.5 sekundy, zalezne od jednostki formularza)
- Timeout: 1000 ms
- Retries: 1
- Max read bit count: 2000
- Max read register count: 125
- Max write register count: 120
- Enabled: ON

Nie pozostawiaj limitow odczytu/zapisu rownych 0. W tej wersji formularza
moze to zapisac zerowe limity i zablokowac odczyty nawet jednego rejestru.
Objaw: puste wartosci na Watch List i zdarzenie
"ModbusTransportException: Invalid number of registers: 1".
Popraw limity w edycji zrodla, zapisz i w razie potrzeby wylacz/wlacz zrodlo.

HMI laczy sie bezposrednio po sieci ot-supervision.
Nie wpisuj tu localhost, host.docker.internal ani portu 8443.
Nie trzeba publikowac portu 502 kontenera na Windowsie.

## 4. Punkty danych

Tank_Level:
- Slave ID: 1
- Register range: Input register
- Offset: 0
- Modbus data type: 2 byte unsigned integer
- Multiplier: 0.01
- Additive: 0
- Settable: OFF
- Enabled: ON
- Format wyswietlania: 2 miejsca po przecinku, jednostka %

Tank_PumpCmd:
- Slave ID: 1
- Register range: Coil status
- Offset: 0
- Typ: Binary, jesli formularz wymaga wyboru
- Settable: OFF
- Enabled: ON
- Tekst 0: WYLACZONA
- Tekst 1: WLACZONA

Offset to adres protokolu od zera. Nie wpisuj 30001 ani 00001.
Uzyj testu odczytu punktu, a potem zapisz i wlacz punkty oraz zrodlo.

Dla Tank_Level wlacz logowanie wszystkich odczytow (All data).
Dla Tank_PumpCmd wystarczy logowanie zmian (On change).
Na poczatek przechowuj historie z ostatnich 7 dni.

## 5. Pierwszy ekran

Najpierw dodaj oba punkty do Watch list i sprawdz zmiany.
Potem Graphical views -> nowy widok Tank_HMI:
- etykieta ZBIORNIK T-101;
- wartosc numeryczna powiazana z Tank_Level;
- wskaznik stanu powiazany z Tank_PumpCmd;
- wykres historii poziomu, ostatnie 5 minut.

Jesli edytor widokow udostepnia komponent poziomu zbiornika, ustaw zakres 0..100
i przypisz Tank_Level. W przeciwnym razie zaczynamy od wartosci numerycznej.
Nazwy komponentow moga sie roznic pomiedzy klasycznym i nowym interfejsem.
Nie dodawaj na tym etapie przycisku wymuszajacego PumpCmd.

## 6. Alarmy

Na punkcie Tank_Level dodaj detektory:
- high limit 75%: WYSOKI POZIOM;
- low limit 25%: NISKI POZIOM.

Progi alarmow sa poza normalnym zakresem 40..60%, wiec przy poprawnej pracy
nie powinny stale sie pojawiac. Sprawdz takze sygnalizacje bledu odczytu zrodla.
Alarm panelu jest informacja dla operatora; sam nie zmienia logiki PLC.

## 7. Kryteria zakonczenia

- Panel pokazuje poziom zgodny z debuggerem PLC (z opoznieniem odswiezania).
- Wskaznik pompy zmienia sie razem z PumpCmd.
- Wykres pokazuje powtarzalne napelnianie i oproznianie.
- Przy zatrzymaniu samego Scada-LTS PLC i proces dalej pracuja.
- Przerwa komunikacji HMI jest widoczna jako blad, nie jako wiarygodny nowy pomiar.

## Weryfikacja przygotowania

Sprawdzono skladnie Compose poleceniem docker compose config --quiet.
Przy przygotowaniu Docker daemon nie byl dostepny, wiec nie potwierdzono pobrania
obrazow, startu aplikacji ani odczytow Scada-LTS w tym srodowisku.

## Zrodla

https://github.com/SCADA-LTS/Scada-LTS/blob/master/docker-compose.yml
https://github.com/SCADA-LTS/Scada-LTS/wiki
https://edge.autonomylogic.com/docs/openplc-editor/examples/modbus-slave-outputs/

