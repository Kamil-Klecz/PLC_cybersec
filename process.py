from dataclasses import dataclass


@dataclass
class Tank:
    capacity_l: float = 100.0
    volume_l: float = 50.0
    pump_flow_l_s: float = 8.0
    outlet_flow_l_s: float = 2.0
    spilled_total_l: float = 0.0

    @property
    def level_pct(self) -> float:
        return 100.0 * self.volume_l / self.capacity_l

    def step(self, pump_on: bool, dt_s: float) -> None:
        inflow_l = self.pump_flow_l_s * dt_s if pump_on else 0.0
        outflow_l = min(self.outlet_flow_l_s * dt_s, self.volume_l + inflow_l)
        next_volume_l = self.volume_l + inflow_l - outflow_l
        self.spilled_total_l += max(0.0, next_volume_l - self.capacity_l)
        self.volume_l = min(self.capacity_l, next_volume_l)

