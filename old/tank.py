import csv
import time
from pathlib import Path

from controller import HysteresisController
from process import Tank


DT_S = 0.1
DURATION_S = 30.0

tank = Tank()
controller = HysteresisController()

output_path = Path(__file__).with_name("measurements.csv")
steps = round(DURATION_S / DT_S)

with output_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([
        "time_s",
        "volume_l",
        "level_pct",
        "pump_on",
        "spilled_total_l",
    ])

    start_time = time.monotonic()

    for step in range(steps + 1):
        time_s = step * DT_S
        deadline = start_time + time_s
        remaining_s = deadline - time.monotonic()

        if remaining_s > 0:
            time.sleep(remaining_s)

        # Pomiar przekazywany do sterownika.
        measured_level_pct = tank.level_pct

        # Polecenie zwracane przez sterownik.
        pump_on = controller.update(measured_level_pct)
        
        print("tank vol:",tank.volume_l)
        print("tank level_pct:",tank.level_pct)
        writer.writerow([
            round(time_s, 3),
            round(tank.volume_l, 3),
            round(tank.level_pct, 3),
            int(pump_on),
            round(tank.spilled_total_l, 3),
        ])

        if step == steps:
            break

        tank.step(pump_on, DT_S)

elapsed_s = time.monotonic() - start_time
print(f"Zapisano pomiary: {output_path}")
print(f"Czas wykonania: {elapsed_s:.2f} s")
print(f"Łączny przelew: {tank.spilled_total_l:.2f} l")