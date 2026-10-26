"""Proces + zdalne I/O. Uruchom jako pierwszy; zatrzymaj Ctrl+C."""
import csv
import time
from pathlib import Path

from pyModbusTCP.server import DataBank, ModbusServer
from process import Tank

HOST = "0.0.0.0"
PORT = 1502
DT_S = 0.1
LEVEL_ADDRESS = 0
PUMP_ADDRESS = 0
LEVEL_SCALE = 100  # 1 jednostka rejestru = 0.01 procenta


def main():
    tank = Tank()
    bank = DataBank(coils_size=1, d_inputs_size=0,
                    h_regs_size=0, i_regs_size=1)
    bank.set_input_registers(LEVEL_ADDRESS, [round(tank.level_pct * LEVEL_SCALE)])
    bank.set_coils(PUMP_ADDRESS, [False])
    server = ModbusServer(host=HOST, port=PORT, no_block=True, data_bank=bank)
    output = Path(__file__).with_name("modbus_measurements.csv")
    try:
        server.start()
        print(f"Serwer: {HOST}:{PORT}. Zatrzymaj Ctrl+C.", flush=True)
        with output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["time_s", "level_pct", "pump_on", "spilled_total_l"])
            start = previous = time.monotonic()
            next_print = start
            while True:
                # Ta komenda obowiazuje w nastepnym przedziale modelu.
                pump_on = bank.get_coils(PUMP_ADDRESS, 1)[0]
                time.sleep(DT_S)
                now = time.monotonic()
                elapsed = now - previous
                previous = now
                # Rzeczywisty uplyw czasu, bez nadrabiania starych krokow.
                tank.step(pump_on, elapsed)
                bank.set_input_registers(
                    LEVEL_ADDRESS, [round(tank.level_pct * LEVEL_SCALE)])
                writer.writerow([round(now - start, 3), round(tank.level_pct, 3),
                                 int(pump_on), round(tank.spilled_total_l, 3)])
                file.flush()
                if now >= next_print:
                    print(f"t={now - start:6.1f}s poziom={tank.level_pct:6.2f}% "
                          f"pompa={int(pump_on)} przelew={tank.spilled_total_l:.2f}l",
                          flush=True)
                    next_print = now + 1.0
    except KeyboardInterrupt:
        print("Zatrzymano proces.")
    finally:
        server.stop()


if __name__ == "__main__":
    main()

