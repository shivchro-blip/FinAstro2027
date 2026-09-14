"""Load the locked conventions once, expose as CONF."""
from __future__ import annotations
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "conventions.yaml"

with CONFIG_PATH.open() as fh:
    CONF = yaml.safe_load(fh)

YEAR = CONF["year"]
PRIMARY = CONF["locations"]["mumbai"]
SECONDARY = CONF["locations"]["new_york"]
