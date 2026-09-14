"""Load the locked conventions once, expose as CONF."""
from __future__ import annotations
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "conventions.yaml"

# Encoding is explicit. The config is UTF-8 -- it carries the source's own
# diacritics ("kalāṃśā") and its em dashes -- and `open()` without an encoding
# uses the LOCALE default, which is cp1252 on this machine. That made the whole
# rule layer fail to import on the first non-ASCII character anywhere in the
# file, which is a property of the host rather than of the config.
with CONFIG_PATH.open(encoding="utf-8") as fh:
    CONF = yaml.safe_load(fh)

YEAR = CONF["year"]
PRIMARY = CONF["locations"]["mumbai"]
SECONDARY = CONF["locations"]["new_york"]
