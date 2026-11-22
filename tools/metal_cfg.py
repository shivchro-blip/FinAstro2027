"""Which metal the big-move / outlook / signal-table scripts run for.

Pass `--metal silver` to any of them (default gold); the choice is kept in the
FINASTRO_METAL environment variable so scripts that load each other agree.
Silver's big-move threshold is 3.5%, the move that is as rare for silver (8.4% of
days, 2000-2026) as 2% is for gold (7.3%).
"""
import os
import sys

if "--metal" in sys.argv:
    _i = sys.argv.index("--metal")
    os.environ["FINASTRO_METAL"] = sys.argv[_i + 1]
    del sys.argv[_i:_i + 2]
METAL = os.environ.get("FINASTRO_METAL", "gold")
assert METAL in ("gold", "silver"), METAL
NAME = METAL.capitalize()
TH = {"gold": 2.0, "silver": 3.5}[METAL]
TICK = {"gold": "GC=F", "silver": "SI=F"}[METAL]
PRICE = {"gold": "gold_GC_F_daily_2000.csv", "silver": "silver_SI_F_daily_2000.csv"}[METAL]
