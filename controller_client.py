"""Regulator komunikuje sie z procesem tylko przez Modbus TCP."""
import time

from pyModbusTCP.client import ModbusClient
from controller import HysteresisController

HOST = "127.0.0.1"
PORT = 1502
POLL_S = 0.1
LEVEL_ADDRESS = 0
PUMP_ADDRESS = 0
LEVEL_SCALE = 100


def main():
    client = ModbusClient(host=HOST, port=PORT, unit_id=1,
                          timeout=1.0, auto_open=False)
    regulator = HysteresisController(low_pct=40.0, high_pct=60.0)
    try:
        if not client.open():
            raise ConnectionError("Brak polaczenia. Uruchom najpierw process_server.py.")
        print("Polaczono z procesem. Zatrzymaj Ctrl+C.", flush=True)
        previous_command = None
        while True:
            registers = client.read_input_registers(LEVEL_ADDRESS, 1)
            if registers is None:
                raise ConnectionError(f"Blad odczytu: {client.last_error_as_txt}; "
                                      f"{client.last_except_as_txt}")
            level_pct = registers[0] / LEVEL_SCALE
            command = regulator.update(level_pct)
            # Wysylamy co cykl, takze gdy stan sie nie zmienia.
            if not client.write_single_coil(PUMP_ADDRESS, command):
                raise ConnectionError(f"Blad zapisu: {client.last_error_as_txt}; "
                                      f"{client.last_except_as_txt}")
            if command != previous_command:
                print(f"Pomiar={level_pct:.2f}% -> pompa={int(command)}", flush=True)
                previous_command = command
            time.sleep(POLL_S)
    except KeyboardInterrupt:
        print("Zatrzymano regulator.")
    except ConnectionError as error:
        print(error)
        raise SystemExit(1)
    finally:
        # Proba porzadkowego wylaczenia, nie watchdog ani gwarancja.
        try:
            if not client.is_open or not client.write_single_coil(PUMP_ADDRESS, False):
                print("Nie potwierdzono wylaczenia pompy. Serwer pamieta ostatnia komende.")
        finally:
            client.close()


if __name__ == "__main__":
    main()

