class HysteresisController:
    def __init__(self, low_pct: float = 40.0, high_pct: float = 60.0):
        if not 0 <= low_pct < high_pct <= 100:
            raise ValueError("Progi muszą spełniać: 0 <= low < high <= 100")

        self.low_pct = low_pct
        self.high_pct = high_pct
        self.pump_on = False

    def update(self, measured_level_pct: float) -> bool:
        if measured_level_pct <= self.low_pct:
            self.pump_on = True
        elif measured_level_pct >= self.high_pct:
            self.pump_on = False

        return self.pump_on