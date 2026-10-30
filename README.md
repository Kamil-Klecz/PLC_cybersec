# PLCSim — laboratorium ICS/OT

Projekt symuluje zbiornik wody w Pythonie, steruje nim przez OpenPLC i dodaje
panel operatorski Scada-LTS. Komunikacja procesu i sterownika wykorzystuje Modbus TCP.

## Dokumentacja

- [Architektura i stan projektu](docs/ARCHITEKTURA.md) — komponenty, połączenia,
  mapa danych, struktura plików oraz plan zabezpieczeń i eksperymentów.
- **[Uruchamianie i zatrzymywanie laboratorium](docs/URUCHAMIANIE.md)** — kolejność
  startu, polecenia PowerShell, adresy, porty, diagnostyka i uruchamianie pojedynczych elementów.
- [Konfiguracja HMI](hmi/README.md) — serwer Modbus PLC, Scada-LTS, punkty danych,
  widok i alarmy. HMI wymaga wykonania opisanej konfiguracji.
- [Wcześniejsze ćwiczenie: Python → Python](docs/ETAP_MODBUS_PYTHON.md) — opis
  poprzedniego etapu; nie jest instrukcją startu obecnego wariantu z PLC.

## Główne elementy

| Element | Plik / nazwa |
|---|---|
| Model procesu | process.py |
| Serwer procesu | process_server.py |
| Projekt OpenPLC | TankControl/ |
| Kontener Runtime | ot-plc |
| Kontenery HMI i bazy | hmi/compose.yaml |
| Klient do wcześniejszego ćwiczenia | controller_client.py |

W głównym wariancie regulatorem jest OpenPLC. Nie uruchamiaj równocześnie
controller_client.py — oba regulatory zapisywałyby polecenie tej samej pompy.

