PROGRAM main
  VAR
    LevelRaw : UINT AT TankLevelInput := 5000;
    LevelPct : REAL := 0.0;
    PumpCmd : BOOL AT TankPumpOutput := FALSE;
  END_VAR

LevelPct := UINT_TO_REAL(LevelRaw) / 100.0;

IF LevelRaw <= 4000 THEN
    PumpCmd := TRUE;
ELSIF LevelRaw >= 6000 THEN
    PumpCmd := FALSE;
END_IF;

END_PROGRAM