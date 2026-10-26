PROGRAM main
  VAR
    LevelPct : REAL := 0.0;
  END_VAR
  VAR
    LevelRaw AT %IW0 : UINT := 5000;
    PumpCmd AT %QX0.0 : BOOL := FALSE;
  END_VAR

  LevelPct := UINT_TO_REAL(LevelRaw) / 100.0;

  IF LevelRaw <= 4000 THEN
      PumpCmd := TRUE;
  ELSIF LevelRaw >= 6000 THEN
      PumpCmd := FALSE;
  END_IF;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 1);
    PROGRAM instance0 WITH task0 : main;
  END_RESOURCE
END_CONFIGURATION
