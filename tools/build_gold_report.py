"""Kept for the command used before: python tools/build_gold_report.py == build_metal_report.py gold."""
import runpy
import sys

sys.argv = [sys.argv[0], "gold"]
runpy.run_path(str(__import__("pathlib").Path(__file__).with_name("build_metal_report.py")), run_name="__main__")
